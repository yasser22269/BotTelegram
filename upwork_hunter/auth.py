# -*- coding: utf-8 -*-
"""
One-time Upwork authorization. Saves tokens to data/tokens.json.
The bot refreshes them automatically afterwards (as long as it keeps running
at least once every ~2 weeks).

Before running: in https://www.upwork.com/developer/keys set the key's
Callback URL to the same value as UPWORK_REDIRECT_URI in .env
(default http://localhost:8888).

Usage:
    python auth.py                 # opens browser, catches the callback
    python auth.py "<full redirect URL or code>"
"""

import os
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from upwork_api import UpworkClient, UpworkAuthError

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

CLIENT_ID     = os.getenv('UPWORK_CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('UPWORK_CLIENT_SECRET', '').strip()
REDIRECT_URI  = os.getenv('UPWORK_REDIRECT_URI', 'http://localhost:8888').strip()

if not CLIENT_ID or not CLIENT_SECRET:
    sys.exit('UPWORK_CLIENT_ID / UPWORK_CLIENT_SECRET missing in .env')

client = UpworkClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


def extract_code(text):
    m = re.search(r'[?&]code=([^&\s]+)', text)
    return m.group(1) if m else text.strip()


def wait_for_callback():
    parsed = urlparse(REDIRECT_URI)
    if parsed.hostname not in ('localhost', '127.0.0.1'):
        return None
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            code = parse_qs(urlparse(self.path).query).get('code', [None])[0]
            if code:
                received['code'] = code
            self.send_response(200 if code else 400)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(('<h2>Done ✅ — you can close this tab.</h2>' if code
                              else '<h2>No code in the URL.</h2>').encode('utf-8'))

        def log_message(self, *args):
            pass

    server = HTTPServer((parsed.hostname, parsed.port or 80), Handler)
    server.timeout = 180
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    return t, received


def main():
    if len(sys.argv) > 1:
        code = extract_code(sys.argv[1])
    else:
        url = client.authorize_url()
        listener = wait_for_callback()
        print('Opening browser to authorize Upwork...\n' + url + '\n')
        webbrowser.open(url)
        code = None
        if listener:
            thread, received = listener
            print('Waiting for the redirect (up to 3 minutes)...')
            thread.join(timeout=185)
            code = received.get('code')
        if not code:
            code = extract_code(input('Paste the full redirect URL (or the code): '))

    if not code:
        sys.exit('No authorization code.')
    try:
        client.exchange_code(code)
    except UpworkAuthError as e:
        sys.exit(str(e))
    print('✅ Upwork tokens saved to data/tokens.json — now run: python bot.py')


if __name__ == '__main__':
    main()
