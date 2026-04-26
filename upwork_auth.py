#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run this script ONCE to authorize Upwork and save tokens to .env automatically.

BEFORE running:
  1. Go to your Upwork app settings at developers.upwork.com
  2. Set Callback URL to:  http://localhost:8888
  3. Save, then run:  python upwork_auth.py
"""

import sys, io, os, re, webbrowser, threading, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from urlparse import urlparse, parse_qs

from dotenv import load_dotenv
load_dotenv()

CLIENT_ID     = os.getenv('UPWORK_CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('UPWORK_CLIENT_SECRET', '').strip()

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: UPWORK_CLIENT_ID / UPWORK_CLIENT_SECRET missing in .env")
    sys.exit(1)

REDIRECT_URI = 'http://localhost:8888'
TOKEN_URL    = 'https://www.upwork.com/api/v3/oauth2/token'
AUTH_URL     = 'https://www.upwork.com/ab/account-security/oauth2/authorize'

auth_code = [None]   # shared between server thread and main thread


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        code   = params.get('code', [None])[0]
        if code:
            auth_code[0] = code
            body = b"<h2>Done! You can close this tab.</h2>"
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code received.")

    def log_message(self, *args):
        pass  # silence server logs


print("=" * 55)
print("  Upwork OAuth 2.0 Setup")
print("=" * 55)
print("\nMake sure your Upwork app Callback URL is set to:")
print("  http://localhost:8888")
print("\nPress Enter to open the browser and authorize...")
try:
    input()
except EOFError:
    pass

# Start local callback server
server = HTTPServer(('localhost', 8888), CallbackHandler)
t = threading.Thread(target=server.handle_request)
t.daemon = True
t.start()

# Open authorization URL
auth_link = (
    f"{AUTH_URL}?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&state=botsetup"
)
print(f"\nOpening browser: {auth_link}\n")
webbrowser.open(auth_link)

# Wait for callback (up to 120s)
print("Waiting for authorization...")
t.join(timeout=120)

code = auth_code[0]
if not code:
    print("\nERROR: No authorization code received.")
    print("Paste the full redirect URL manually:")
    try:
        url = input("> ").strip()
    except EOFError:
        url = ''
    m = re.search(r'[?&]code=([^&]+)', url)
    code = m.group(1) if m else url.strip()

if not code:
    print("ERROR: No code provided.")
    sys.exit(1)

print(f"\nCode received. Exchanging for tokens...")

# Exchange code for tokens
resp = requests.post(TOKEN_URL, data={
    'grant_type':    'authorization_code',
    'code':          code,
    'client_id':     CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri':  REDIRECT_URI,
}, timeout=15)

if resp.status_code != 200:
    print(f"ERROR {resp.status_code}: {resp.text}")
    sys.exit(1)

tokens        = resp.json()
access_token  = tokens.get('access_token', '')
refresh_token = tokens.get('refresh_token', '')

if not access_token:
    print(f"ERROR: no access_token in response: {tokens}")
    sys.exit(1)

# Save to .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'UPWORK_ACCESS_TOKEN=.*',  f'UPWORK_ACCESS_TOKEN={access_token}',  content)
content = re.sub(r'UPWORK_REFRESH_TOKEN=.*', f'UPWORK_REFRESH_TOKEN={refresh_token}', content)

with open(env_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Tokens saved to .env successfully!")
print("   Now run: python bot_working.py")
