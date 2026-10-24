"""Crash-safe state and health reporting for the deployed bot."""
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def safe_error(error):
    return re.sub(r'(?<!\d)\d{7,}:[A-Za-z0-9_-]+', '[REDACTED]', str(error))


class RedactTokens:
    def filter(self, record):
        record.msg = safe_error(record.getMessage())
        record.args = ()
        return True


class Health:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        try:
            self.state = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.state = {}

    def update(self, **values):
        with self.lock:
            self.state.update(values)
            atomic_json(self.path, self.state)

    def snapshot(self):
        with self.lock:
            return dict(self.state)

    def failed(self, error, interval):
        state = self.snapshot()
        failures = state.get('scrape_failures', 0) + 1
        status = getattr(getattr(error, 'response', None), 'status_code', None)
        base = max(interval, 300 if status in (403, 429) else 30)
        delay = min(1800, base * 2 ** min(failures - 1, 6))
        self.update(scrape_failures=failures, scrape_error=safe_error(error),
                    scrape_error_at=time.time(), scrape_retry_at=time.time() + delay)
        return delay


def stalled(state, now=None):
    now = time.time() if now is None else now
    started = state.get('started_at', 0)
    if not started or now - started < 180:
        return False
    if now - state.get('poll_ok_at', started) > 180:
        return True
    # A source rejecting requests is degraded, not a reason to restart and hammer it.
    next_attempt = state.get('scrape_retry_at', started)
    return now > max(next_attempt, state.get('scrape_attempt_at', started)) + 180


if __name__ == '__main__':
    import sys
    state = Health(Path(__file__).parent / 'logs' / 'health.json').snapshot()
    if '--check' in sys.argv:
        sys.exit(1 if stalled(state) else 0)
    print(json.dumps(state, ensure_ascii=False, indent=2))
