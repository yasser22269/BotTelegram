"""Offline regression checks. Never connects to Telegram or sends messages."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

import bot_working as bot
from bot_runtime import Health, atomic_json, safe_error, stalled


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.health = Health(self.path / 'health.json')
        self.patches = [
            patch.object(bot, 'HEALTH', self.health),
            patch.object(bot, 'DATA_FILE', str(self.path / 'users.json')),
            patch.object(bot, 'users', {}),
            patch.object(bot, 'seen_ids', {100}),
            patch.object(bot, 'upwork_seen_ids', set()),
            patch.object(bot, 'pending_projects', {}),
            patch.object(bot.time, 'sleep'),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def response(self, status=200, html=''):
        response = requests.Response()
        response.status_code = status
        response.url = 'https://mostaql.com/projects'
        response._content = html.encode()
        response.encoding = 'utf-8'
        return response

    def test_listing_rejects_http_errors(self):
        for status in (403, 429, 503):
            with self.subTest(status=status), patch.object(bot.requests, 'get', return_value=self.response(status)):
                with self.assertRaises(requests.HTTPError):
                    bot.fetch_listing()

    def test_listing_rejects_empty_or_changed_html(self):
        for html in ('', '<title>Access denied</title>'):
            with patch.object(bot.requests, 'get', return_value=self.response(html=html)):
                with self.assertRaises(ValueError):
                    bot.fetch_listing()

    def test_listing_parses_valid_projects(self):
        html = '<h2><a href="/project/101-example">Example</a></h2>'
        with patch.object(bot.requests, 'get', return_value=self.response(html=html)):
            self.assertEqual(bot.fetch_listing(), {101: 'https://mostaql.com/project/101-example'})

    def test_project_rejects_http_error(self):
        with patch.object(bot.requests, 'get', return_value=self.response(403)):
            with self.assertRaises(requests.HTTPError):
                bot.scrape_project('https://mostaql.com/project/101-example')

    def test_project_rejects_invalid_html(self):
        with patch.object(bot.requests, 'get', return_value=self.response(html='<title>Maintenance</title>')):
            with self.assertRaises(ValueError):
                bot.scrape_project('https://mostaql.com/project/101-example')

    def test_failed_send_is_persisted_and_retried_after_restart(self):
        client = Mock()
        client.send_message.side_effect = RuntimeError('temporary Telegram failure')
        project = {'category_id': '2', 'title': 'Example'}
        with patch.object(bot, 'fetch_listing', return_value={101: 'url'}), \
                patch.object(bot, 'scrape_project', return_value=project), \
                patch.object(bot, 'format_scraped', return_value='message'):
            with self.assertRaises(RuntimeError):
                bot.scrape_cycle(client)
            self.assertNotIn(101, bot.seen_ids)
            self.assertEqual(json.loads(Path(bot.DATA_FILE).read_text())['pending_projects'], {'101': 'url'})
            bot.pending_projects.clear()
            bot.load_data()
            # Retry must survive the project disappearing from the latest listing.
            client.send_message.side_effect = None
            with patch.object(bot, 'fetch_listing', return_value={100: 'old'}):
                bot.scrape_cycle(client)
            self.assertIn(101, bot.seen_ids)
            self.assertEqual(bot.pending_projects, {})
            self.assertEqual(client.send_message.call_count, 2)

    def test_restart_does_not_seed_away_unseen_projects(self):
        client = Mock()
        with patch.object(bot, 'fetch_listing', return_value={101: 'url'}), \
                patch.object(bot, 'scrape_project', return_value={'category_id': '2', 'title': 'Example'}), \
                patch.object(bot, 'format_scraped', return_value='message'):
            bot.scrape_cycle(client)
            bot.scrape_cycle(client)
        client.send_message.assert_called_once()

    def test_one_invalid_project_does_not_block_later_projects(self):
        client = Mock()
        with patch.object(bot, 'fetch_listing', return_value={101: 'bad', 102: 'good'}), \
                patch.object(bot, 'scrape_project', side_effect=[ValueError('invalid'), {'category_id': '2', 'title': 'Good'}]), \
                patch.object(bot, 'format_scraped', return_value='message'):
            with self.assertRaises(ValueError):
                bot.scrape_cycle(client)
        self.assertNotIn(101, bot.seen_ids)
        self.assertIn(102, bot.seen_ids)
        self.assertEqual(bot.pending_projects, {101: 'bad'})

    def test_first_install_seeds_without_flooding(self):
        bot.seen_ids.clear()
        client = Mock()
        with patch.object(bot, 'fetch_listing', return_value={101: 'url'}):
            bot.scrape_cycle(client)
        client.send_message.assert_not_called()
        self.assertIn(101, bot.seen_ids)

    def test_fetch_failure_preserves_seen_state(self):
        with patch.object(bot, 'fetch_listing', side_effect=requests.Timeout('offline')):
            with self.assertRaises(requests.Timeout):
                bot.scrape_cycle(Mock())
        self.assertEqual(bot.seen_ids, {100})

    def test_backoff_survives_restart_and_is_capped(self):
        error = requests.HTTPError('403 Forbidden', response=self.response(403))
        self.assertEqual(self.health.failed(error, 60), 300)
        restored = Health(self.health.path)
        self.assertEqual(restored.failed(error, 60), 600)
        for _ in range(10):
            delay = restored.failed(error, 60)
        self.assertEqual(delay, 1800)

    def test_atomic_write_failure_keeps_previous_file(self):
        path = self.path / 'data.json'
        atomic_json(path, {'old': True})
        with patch('bot_runtime.os.replace', side_effect=OSError('disk error')):
            with self.assertRaises(OSError):
                atomic_json(path, {'new': True})
        self.assertEqual(json.loads(path.read_text()), {'old': True})
        self.assertEqual(list(self.path.glob('data.json.*')), [])

    def test_stalled_poll_is_detected_but_source_backoff_is_not(self):
        state = {'started_at': 1000, 'poll_ok_at': 1990, 'scrape_attempt_at': 1500,
                 'scrape_retry_at': 3300, 'scrape_error': '403 Forbidden'}
        self.assertFalse(stalled(state, now=2000))
        state['poll_ok_at'] = 1500
        self.assertTrue(stalled(state, now=2000))

    def test_stalled_scraper_is_detected(self):
        state = {'started_at': 1000, 'poll_ok_at': 1990, 'scrape_attempt_at': 1500,
                 'scrape_retry_at': 1600}
        self.assertTrue(stalled(state, now=2000))

    def test_error_redacts_telegram_token(self):
        self.assertEqual(safe_error('/bot123456789:fake_secret/getUpdates'), '/bot[REDACTED]/getUpdates')


if __name__ == '__main__':
    unittest.main()
