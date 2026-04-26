#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    python upwork_exchange.py CODE_OR_FULL_URL
"""
import sys, io, os, re, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID     = os.getenv('UPWORK_CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('UPWORK_CLIENT_SECRET', '').strip()
REDIRECT_URI  = 'http://localhost:8888'
TOKEN_URL     = 'https://www.upwork.com/api/v3/oauth2/token'

if len(sys.argv) < 2:
    print("Usage: python upwork_exchange.py CODE_OR_FULL_URL")
    sys.exit(1)

arg = sys.argv[1].strip()
m   = re.search(r'[?&]code=([^&]+)', arg)
code = m.group(1) if m else arg

print(f"Exchanging code: {code[:15]}...")

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
    print(f"ERROR: {tokens}")
    sys.exit(1)

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'UPWORK_ACCESS_TOKEN=.*',  f'UPWORK_ACCESS_TOKEN={access_token}',  content)
content = re.sub(r'UPWORK_REFRESH_TOKEN=.*', f'UPWORK_REFRESH_TOKEN={refresh_token}', content)

with open(env_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Tokens saved to .env")
print(f"  access_token:  {access_token[:20]}...")
print(f"  refresh_token: {refresh_token[:20]}...")
print("\nNow run: python bot_working.py")
