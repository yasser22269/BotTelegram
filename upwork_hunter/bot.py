# -*- coding: utf-8 -*-
"""
Upwork Hunter — personal Telegram bot that pushes new Upwork jobs in near
real time, filtered by your own settings (like Offers Hunter, but yours).

Run:  python bot.py
"""

import html
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from upwork_api import CATEGORIES, DATA_DIR, UpworkAuthError, UpworkClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))
os.makedirs(DATA_DIR, exist_ok=True)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
ADMIN_ID       = os.getenv('ADMIN_ID', '').strip()
ALLOWED_CHATS  = {int(x) for x in (os.getenv('ALLOWED_CHAT_IDS', '') or ADMIN_ID).replace(' ', '').split(',') if x}
MAX_JOB_AGE    = int(os.getenv('MAX_JOB_AGE_MINUTES', '60')) * 60

SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
SEEN_FILE     = os.path.join(DATA_DIR, 'seen.json')

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler(os.path.join(DATA_DIR, 'bot.log'), encoding='utf-8')],
)
log = logging.getLogger('bot')

DEFAULT_SETTINGS = {
    'paused':            False,
    'interval':          int(os.getenv('POLL_INTERVAL', '60')),
    'queries':           [],                         # empty = all jobs in the selected categories
    'categories':        ['531770282580668418'],     # Web, Mobile & Software Dev
    'job_type':          'all',                      # all | hourly | fixed
    'min_hourly':        0,
    'min_fixed':         0,
    'min_client_spent':  0,
    'verified_only':     False,
    'include_no_budget': True,
    'exclude_countries': [],
    'exclude_words':     [],
}

lock = threading.RLock()


def load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


settings = {**DEFAULT_SETTINGS, **load_json(SETTINGS_FILE, {})}
seen     = load_json(SEEN_FILE, [])
seen_set = set(seen)


def save_settings():
    with lock:
        save_json(SETTINGS_FILE, settings)


def mark_seen(job_id):
    if job_id not in seen_set:
        seen_set.add(job_id)
        seen.append(job_id)


def save_seen():
    with lock:
        del seen[:-5000]
        seen_set.intersection_update(seen)
        save_json(SEEN_FILE, seen)


# ── Telegram ──────────────────────────────────────────────────────────────────
TG_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/'


def tg(method, timeout=30, **params):
    for _ in range(3):
        try:
            r = requests.post(TG_URL + method, json=params, timeout=timeout)
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            log.warning('Telegram %s failed: %s', method, e)
            time.sleep(3)
            continue
        if data.get('ok'):
            return data.get('result')
        retry = (data.get('parameters') or {}).get('retry_after')
        if retry:
            time.sleep(retry + 1)
            continue
        log.warning('Telegram %s error: %s', method, data.get('description'))
        return None
    return None


def send(chat_id, text, buttons=None):
    params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML',
              'disable_web_page_preview': True}
    if buttons:
        params['reply_markup'] = {'inline_keyboard': buttons}
    return tg('sendMessage', **params)


def broadcast(text, buttons=None):
    for chat_id in ALLOWED_CHATS:
        send(chat_id, text, buttons)


# ── Job helpers ───────────────────────────────────────────────────────────────
def money(m):
    try:
        return float((m or {}).get('rawValue') or 0)
    except (TypeError, ValueError):
        return 0.0


def fmt_money(v):
    return f"${v:,.0f}" if v == int(v) else f"${v:,.2f}"


def job_kind(job):
    if money(job.get('hourlyBudgetMin')) or money(job.get('hourlyBudgetMax')) or job.get('hourlyBudgetType'):
        return 'hourly'
    if money(job.get('amount')):
        return 'fixed'
    return 'unknown'


def pretty(value):
    if not value:
        return ''
    value = str(value)
    if '_' in value or value.isupper():
        value = value.replace('_', ' ').title()
    return value


def parse_time(value):
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def job_url(job):
    cipher = job.get('ciphertext') or ''
    if cipher:
        return f"https://www.upwork.com/jobs/{cipher if cipher.startswith('~') else '~' + cipher}"
    return f"https://www.upwork.com/jobs/~{job.get('id')}"


def passes(job, s):
    client  = job.get('client') or {}
    kind    = job_kind(job)
    country = ((client.get('location') or {}).get('country') or '').lower()
    text    = f"{job.get('title', '')} {job.get('description', '')}".lower()

    if s['job_type'] != 'all' and kind not in (s['job_type'], 'unknown'):
        return False
    if kind == 'unknown' and not s['include_no_budget']:
        return False
    if kind == 'hourly' and s['min_hourly']:
        top = max(money(job.get('hourlyBudgetMax')), money(job.get('hourlyBudgetMin')))
        if top and top < s['min_hourly']:
            return False
        if not top and not s['include_no_budget']:
            return False
    if kind == 'fixed' and s['min_fixed'] and money(job.get('amount')) < s['min_fixed']:
        return False
    if s['verified_only'] and (client.get('verificationStatus') or '').upper() != 'VERIFIED':
        return False
    if s['min_client_spent'] and money(client.get('totalSpent')) < s['min_client_spent']:
        return False
    if country and country in [c.lower() for c in s['exclude_countries']]:
        return False
    if any(w.lower() in text for w in s['exclude_words']):
        return False
    return True


def format_job(job):
    client  = job.get('client') or {}
    kind    = job_kind(job)
    e       = lambda v: html.escape(str(v))
    desc    = (job.get('description') or '').strip()
    if len(desc) > 1800:
        desc = desc[:1800].rstrip() + '…'

    lines = [f"<b>{e(job.get('title', '').strip())}</b>", '', e(desc), '']

    posted = parse_time(job.get('createdDateTime') or job.get('publishedDateTime'))
    if posted:
        lines.append(f"🕐 Posted On: {posted.astimezone().strftime('%Y-%m-%d %H:%M:%S')}")
    cat = ' | '.join(x for x in (pretty(job.get('subcategory')), pretty(job.get('category'))) if x)
    if cat:
        lines.append(f"🔧 Category: {e(cat)}")
    loc = client.get('location') or {}
    if loc.get('country'):
        lines.append(f"🌍 Country: {e(loc['country'])}")

    if kind == 'hourly':
        lo, hi = money(job.get('hourlyBudgetMin')), money(job.get('hourlyBudgetMax'))
        rate = ' - '.join(fmt_money(v) for v in (lo, hi) if v) or 'Not specified'
        lines.append(f"💰 Hourly: {rate}")
    elif kind == 'fixed':
        lines.append(f"💰 Fixed: {fmt_money(money(job.get('amount')))}")
    else:
        lines.append('💰 Budget: Not specified')

    extra = [pretty(job.get('experienceLevel')), job.get('durationLabel') or pretty(job.get('duration'))]
    extra = [x for x in extra if x]
    if extra:
        lines.append(f"🎓 {e(' · '.join(extra))}")

    skills = [s.get('prettyName') or s.get('name') for s in job.get('skills') or []]
    if skills:
        lines.append(f"🔑 Keywords: {e(', '.join(x for x in skills if x))}")

    spent = money(client.get('totalSpent'))
    client_bits = [f"Spent: {fmt_money(spent)}"]
    if client.get('totalHires'):
        client_bits.append(f"Hires: {client['totalHires']}")
    if client.get('totalPostedJobs'):
        client_bits.append(f"Jobs: {client['totalPostedJobs']}")
    if client.get('totalFeedback'):
        client_bits.append(f"⭐ {float(client['totalFeedback']):.1f}")
    lines.append(f"👔 {' | '.join(client_bits)}")

    if job.get('totalApplicants') is not None:
        lines.append(f"👥 Proposals: {job['totalApplicants']}")
    if (client.get('verificationStatus') or '').upper() != 'VERIFIED':
        lines.append('⚠️ Payment not verified')

    text = '\n'.join(lines)
    return text[:4000], [[{'text': '🔗 Open on Upwork', 'url': job_url(job)}]]


# ── Upwork polling ────────────────────────────────────────────────────────────
upwork = UpworkClient(os.getenv('UPWORK_CLIENT_ID', '').strip(),
                      os.getenv('UPWORK_CLIENT_SECRET', '').strip(),
                      os.getenv('UPWORK_REDIRECT_URI', 'http://localhost:8888').strip())
status = {'last_poll': None, 'last_error': None, 'sent': 0, 'auth_alerted': False}


def fetch_jobs(s):
    jobs = {}
    for q in s['queries'] or ['']:
        for node in upwork.search(q, s['categories']):
            jobs[node['id']] = node
    return sorted(jobs.values(), key=lambda j: j.get('createdDateTime') or '')


def poll_once():
    with lock:
        s = json.loads(json.dumps(settings))
    jobs = fetch_jobs(s)
    now  = datetime.now(timezone.utc)
    sent = 0
    for job in jobs:
        if job['id'] in seen_set:
            continue
        mark_seen(job['id'])
        posted = parse_time(job.get('createdDateTime'))
        if posted and (now - posted).total_seconds() > MAX_JOB_AGE:
            continue
        if passes(job, s):
            text, buttons = format_job(job)
            broadcast(text, buttons)
            sent += 1
            log.info('Sent %s | %s', job['id'], job.get('title', '')[:60])
    save_seen()
    status.update(last_poll=datetime.now(), last_error=None, sent=status['sent'] + sent)
    return len(jobs), sent


def poller():
    while True:
        with lock:
            paused, interval = settings['paused'], max(20, int(settings['interval']))
        if not paused:
            try:
                if not upwork.has_tokens() and not upwork.reload_tokens():
                    raise UpworkAuthError('Not authorized yet — run: python auth.py')
                total, sent = poll_once()
                status['auth_alerted'] = False
                log.info('Poll: %d jobs fetched, %d sent', total, sent)
            except UpworkAuthError as e:
                status['last_error'] = str(e)
                log.error('Auth: %s', e)
                if not status['auth_alerted']:
                    broadcast(f"🔐 Upwork authorization problem:\n<code>{html.escape(str(e))}</code>\n\n"
                              f"Run <code>python auth.py</code> on your PC.")
                    status['auth_alerted'] = True
                upwork.reload_tokens()
            except Exception as e:
                status['last_error'] = str(e)
                log.exception('Poll failed')
        time.sleep(interval)


# ── Settings UI ───────────────────────────────────────────────────────────────
def on_off(v):
    return '✅ ON' if v else '❌ OFF'


def settings_text():
    s = settings
    cats = ', '.join(CATEGORIES.get(c, c) for c in s['categories']) or 'All categories'
    q    = '\n'.join(f"  {i}. <code>{html.escape(x)}</code>" for i, x in enumerate(s['queries'], 1)) or '  (none — all jobs in categories)'
    return (
        f"⚙️ <b>Settings</b> — {'⏸ PAUSED' if s['paused'] else '▶️ Running'} (every {s['interval']}s)\n\n"
        f"🔎 <b>Search queries</b>:\n{q}\n\n"
        f"📂 Categories: {html.escape(cats)}\n"
        f"💼 Job type: {s['job_type']}\n"
        f"💵 Min hourly: {fmt_money(s['min_hourly'])} | Min fixed: {fmt_money(s['min_fixed'])}\n"
        f"👔 Min client spent: {fmt_money(s['min_client_spent'])}\n"
        f"✔️ Verified payment only: {on_off(s['verified_only'])}\n"
        f"❔ Include jobs without budget: {on_off(s['include_no_budget'])}\n"
        f"🚫 Excluded countries: {html.escape(', '.join(s['exclude_countries']) or '—')}\n"
        f"🚫 Excluded words: {html.escape(', '.join(s['exclude_words']) or '—')}"
    )


def settings_keyboard():
    s = settings
    return [
        [{'text': '▶️ Resume' if s['paused'] else '⏸ Pause', 'callback_data': 'pause'},
         {'text': f"💼 Type: {s['job_type']}", 'callback_data': 'type'}],
        [{'text': f"✔️ Verified only: {'ON' if s['verified_only'] else 'OFF'}", 'callback_data': 'verified'},
         {'text': f"❔ No-budget: {'ON' if s['include_no_budget'] else 'OFF'}", 'callback_data': 'nobudget'}],
        [{'text': '📂 Categories', 'callback_data': 'cats'},
         {'text': '🔄 Refresh', 'callback_data': 'refresh'}],
    ]


def categories_keyboard():
    rows = [[{'text': f"{'✅' if cid in settings['categories'] else '▫️'} {name}", 'callback_data': f'cat:{cid}'}]
            for cid, name in CATEGORIES.items()]
    rows.append([{'text': '⬅️ Back', 'callback_data': 'back'}])
    return rows


HELP = """🤖 <b>Upwork Hunter</b> — your personal Upwork job feed

<b>Main</b>
/settings — show settings + buttons
/status — bot / API status
/latest 5 — show the latest N matching jobs now
/pause  /resume

<b>Search</b> (each query is searched separately)
/addkw <i>laravel OR php</i> — add a search query
/delkw <i>number or text</i> — remove a query
/clearkw — remove all queries

<b>Filters</b>
/type all|hourly|fixed
/minhourly 15 · /minfixed 100 · /minspent 500
/verified on|off · /nobudget on|off
/exc <i>India</i> — toggle excluded country
/exw <i>wordpress</i> — toggle excluded word
/interval 60 — seconds between checks"""


def set_number(chat_id, key, arg):
    try:
        settings[key] = max(0, float(arg)) if key != 'interval' else max(20, int(arg))
    except ValueError:
        return send(chat_id, '❌ Send a number, e.g. <code>/minhourly 15</code>')
    save_settings()
    send(chat_id, f"✅ {key} = {settings[key]}")


def toggle_item(chat_id, key, value):
    if not value:
        return send(chat_id, '❌ Missing value')
    items = settings[key]
    match = next((x for x in items if x.lower() == value.lower()), None)
    if match:
        items.remove(match)
        send(chat_id, f"➖ Removed from {key}: {html.escape(match)}")
    else:
        items.append(value)
        send(chat_id, f"➕ Added to {key}: {html.escape(value)}")
    save_settings()


def handle_command(chat_id, text):
    cmd, _, arg = text.strip().partition(' ')
    cmd, arg = cmd.split('@')[0].lower(), arg.strip()

    with lock:
        if cmd in ('/start', '/help'):
            send(chat_id, HELP)
        elif cmd == '/settings':
            send(chat_id, settings_text(), settings_keyboard())
        elif cmd == '/status':
            lp = status['last_poll'].strftime('%H:%M:%S') if status['last_poll'] else 'never'
            err = html.escape(status['last_error'] or 'none')
            send(chat_id, f"📊 Last check: {lp}\n📨 Sent this session: {status['sent']}\n"
                          f"🔐 Upwork authorized: {'yes' if upwork.has_tokens() else 'no'}\n⚠️ Last error: {err}")
        elif cmd in ('/pause', '/resume'):
            settings['paused'] = cmd == '/pause'
            save_settings()
            send(chat_id, '⏸ Paused' if settings['paused'] else '▶️ Resumed')
        elif cmd == '/addkw':
            if not arg:
                return send(chat_id, '❌ Example: <code>/addkw laravel OR php</code>')
            if arg not in settings['queries']:
                settings['queries'].append(arg)
                save_settings()
            send(chat_id, f"➕ Query added: <code>{html.escape(arg)}</code>")
        elif cmd == '/delkw':
            q = settings['queries']
            target = q[int(arg) - 1] if arg.isdigit() and 0 < int(arg) <= len(q) else arg
            if target in q:
                q.remove(target)
                save_settings()
                send(chat_id, f"➖ Query removed: <code>{html.escape(target)}</code>")
            else:
                send(chat_id, '❌ Not found — see /settings')
        elif cmd == '/clearkw':
            settings['queries'] = []
            save_settings()
            send(chat_id, '🧹 All queries cleared')
        elif cmd == '/type':
            if arg not in ('all', 'hourly', 'fixed'):
                return send(chat_id, '❌ Use: /type all | hourly | fixed')
            settings['job_type'] = arg
            save_settings()
            send(chat_id, f"✅ Job type: {arg}")
        elif cmd in ('/verified', '/nobudget'):
            key = 'verified_only' if cmd == '/verified' else 'include_no_budget'
            settings[key] = arg.lower() in ('on', '1', 'yes', 'true')
            save_settings()
            send(chat_id, f"✅ {key}: {on_off(settings[key])}")
        elif cmd in ('/minhourly', '/minfixed', '/minspent', '/interval'):
            key = {'/minhourly': 'min_hourly', '/minfixed': 'min_fixed',
                   '/minspent': 'min_client_spent', '/interval': 'interval'}[cmd]
            set_number(chat_id, key, arg)
        elif cmd == '/exc':
            toggle_item(chat_id, 'exclude_countries', arg)
        elif cmd == '/exw':
            toggle_item(chat_id, 'exclude_words', arg)
        elif cmd == '/latest':
            threading.Thread(target=send_latest, args=(chat_id, arg), daemon=True).start()
        else:
            send(chat_id, 'Unknown command — /help')


def send_latest(chat_id, arg):
    n = int(arg) if arg.isdigit() else 5
    try:
        with lock:
            s = json.loads(json.dumps(settings))
        jobs = [j for j in reversed(fetch_jobs(s)) if passes(j, s)][:n]
    except Exception as e:
        return send(chat_id, f"❌ {html.escape(str(e))}")
    if not jobs:
        return send(chat_id, 'No matching jobs right now.')
    for job in reversed(jobs):
        text, buttons = format_job(job)
        send(chat_id, text, buttons)


def handle_callback(cq):
    chat_id = cq['message']['chat']['id']
    msg_id  = cq['message']['message_id']
    data    = cq.get('data', '')
    with lock:
        if data == 'pause':
            settings['paused'] = not settings['paused']
        elif data == 'type':
            order = ['all', 'hourly', 'fixed']
            settings['job_type'] = order[(order.index(settings['job_type']) + 1) % 3]
        elif data == 'verified':
            settings['verified_only'] = not settings['verified_only']
        elif data == 'nobudget':
            settings['include_no_budget'] = not settings['include_no_budget']
        elif data.startswith('cat:'):
            cid = data[4:]
            cats = settings['categories']
            cats.remove(cid) if cid in cats else cats.append(cid)
        save_settings()

        if data == 'cats' or data.startswith('cat:'):
            text = '📂 <b>Categories</b> (none selected = all of Upwork)'
            keyboard = categories_keyboard()
        else:
            text, keyboard = settings_text(), settings_keyboard()
    tg('answerCallbackQuery', callback_query_id=cq['id'])
    tg('editMessageText', chat_id=chat_id, message_id=msg_id, text=text, parse_mode='HTML',
       disable_web_page_preview=True, reply_markup={'inline_keyboard': keyboard})


def updates_loop():
    offset = None
    while True:
        for u in tg_get_updates(offset):
            offset = u['update_id'] + 1
            try:
                if 'callback_query' in u:
                    cq = u['callback_query']
                    if cq['message']['chat']['id'] in ALLOWED_CHATS:
                        handle_callback(cq)
                elif 'message' in u and 'text' in u['message']:
                    m = u['message']
                    chat_id = m['chat']['id']
                    if chat_id in ALLOWED_CHATS:
                        handle_command(chat_id, m['text'])
                    else:
                        send(chat_id, f"🔒 Private bot.\nYour chat ID: <code>{chat_id}</code>\n"
                                      f"Put it in ADMIN_ID inside .env and restart the bot.")
            except Exception:
                log.exception('Update handling failed')


def tg_get_updates(offset):
    try:
        r = requests.post(TG_URL + 'getUpdates', timeout=65, json={
            'timeout': 50, 'offset': offset, 'allowed_updates': ['message', 'callback_query']})
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        log.warning('getUpdates failed: %s', e)
        time.sleep(5)
        return []
    if not data.get('ok'):
        log.error('getUpdates: %s', data.get('description'))
        time.sleep(10)
        return []
    return data['result']


def main():
    if not TELEGRAM_TOKEN:
        sys.exit('TELEGRAM_TOKEN missing in .env (create a NEW bot with @BotFather)')
    me = tg('getMe')
    if not me:
        sys.exit('Invalid TELEGRAM_TOKEN')
    tg('deleteWebhook')
    tg('setMyCommands', commands=[
        {'command': 'settings', 'description': 'Settings & filters'},
        {'command': 'latest',   'description': 'Latest matching jobs'},
        {'command': 'status',   'description': 'Bot status'},
        {'command': 'help',     'description': 'All commands'},
    ])
    log.info('Bot @%s started | chats: %s', me['username'], ALLOWED_CHATS or 'none (send /start to get your ID)')
    if not upwork.has_tokens():
        log.warning('Upwork not authorized yet — run: python auth.py')
    threading.Thread(target=poller, daemon=True).start()
    updates_loop()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
