# -*- coding: utf-8 -*-
"""Upwork official API client: OAuth 2.0 token handling + GraphQL job search."""

import json
import logging
import os
import threading
import time

import requests

log = logging.getLogger('upwork')

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, 'data')
TOKEN_FILE = os.path.join(DATA_DIR, 'tokens.json')

AUTH_URL    = 'https://www.upwork.com/ab/account-security/oauth2/authorize'
TOKEN_URL   = 'https://www.upwork.com/api/v3/oauth2/token'
GRAPHQL_URL = 'https://api.upwork.com/graphql'

# Top-level Upwork categories (IDs used by categoryIds_any)
CATEGORIES = {
    '531770282580668418': 'Web, Mobile & Software Dev',
    '531770282580668419': 'IT & Networking',
    '531770282580668420': 'Data Science & Analytics',
    '531770282580668421': 'Design & Creative',
    '531770282580668422': 'Sales & Marketing',
    '531770282580668423': 'Writing',
    '531770282580668416': 'Admin Support',
    '531770282580668417': 'Customer Service',
    '531770282584862720': 'Translation',
    '531770282584862721': 'Accounting & Consulting',
    '531770282584862722': 'Engineering & Architecture',
    '531770282584862723': 'Legal',
}

_MONEY = '{ rawValue currency displayValue }'

FULL_FIELDS = f"""
  id ciphertext title description createdDateTime publishedDateTime
  category subcategory experienceLevel duration durationLabel engagement
  totalApplicants
  skills {{ name prettyName }}
  amount {_MONEY}
  hourlyBudgetType
  hourlyBudgetMin {_MONEY}
  hourlyBudgetMax {_MONEY}
  client {{
    totalHires totalPostedJobs totalReviews totalFeedback verificationStatus
    totalSpent {_MONEY}
    location {{ country city timezone }}
  }}
"""

# Used automatically if Upwork rejects one of the optional fields above
MIN_FIELDS = f"""
  id ciphertext title description createdDateTime category subcategory
  skills {{ name prettyName }}
  amount {_MONEY}
  hourlyBudgetMin {_MONEY}
  hourlyBudgetMax {_MONEY}
  client {{ verificationStatus totalSpent {_MONEY} location {{ country }} }}
"""

SEARCH_QUERY = """
query search($filter: MarketplaceJobPostingsSearchFilter,
             $searchType: MarketplaceJobPostingSearchType,
             $sort: [MarketplaceJobPostingSearchSortAttribute]) {
  marketplaceJobPostingsSearch(marketPlaceJobFilter: $filter,
                               searchType: $searchType,
                               sortAttributes: $sort) {
    totalCount
    edges { node { %s } }
  }
}
"""


class UpworkAuthError(Exception):
    """Tokens are missing or can no longer be refreshed — run auth.py again."""


class UpworkClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id     = client_id
        self.client_secret = client_secret
        self.redirect_uri  = redirect_uri
        self._lock   = threading.Lock()
        self._tokens = self._load_tokens()
        self._fields = FULL_FIELDS

    # ── tokens ────────────────────────────────────────────────────────────────
    @staticmethod
    def _load_tokens():
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_tokens(self, payload):
        os.makedirs(DATA_DIR, exist_ok=True)
        tokens = {
            'access_token':  payload['access_token'],
            'refresh_token': payload.get('refresh_token') or self._tokens.get('refresh_token', ''),
            'expires_at':    int(time.time()) + int(payload.get('expires_in', 86400)),
        }
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2)
        self._tokens = tokens

    def has_tokens(self):
        return bool(self._tokens.get('access_token'))

    def reload_tokens(self):
        """Pick up tokens written by auth.py while the bot is running."""
        with self._lock:
            self._tokens = self._load_tokens()
        return self.has_tokens()

    def authorize_url(self, state='upwork-hunter'):
        return (f"{AUTH_URL}?response_type=code&client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}&state={state}")

    def exchange_code(self, code):
        resp = requests.post(TOKEN_URL, data={
            'grant_type':    'authorization_code',
            'code':          code,
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri':  self.redirect_uri,
        }, timeout=20)
        if resp.status_code != 200:
            raise UpworkAuthError(f"Token exchange failed {resp.status_code}: {resp.text[:300]}")
        self._save_tokens(resp.json())

    def _refresh(self):
        refresh_token = self._tokens.get('refresh_token')
        if not refresh_token:
            raise UpworkAuthError('No refresh token — run: python auth.py')
        resp = requests.post(TOKEN_URL, data={
            'grant_type':    'refresh_token',
            'refresh_token': refresh_token,
            'client_id':     self.client_id,
            'client_secret': self.client_secret,
        }, timeout=20)
        if resp.status_code != 200:
            raise UpworkAuthError(f"Token refresh failed {resp.status_code}: {resp.text[:300]}")
        self._save_tokens(resp.json())
        log.info('Upwork access token refreshed')

    def _access_token(self):
        with self._lock:
            if not self.has_tokens():
                raise UpworkAuthError('Not authorized yet — run: python auth.py')
            if self._tokens.get('expires_at', 0) - time.time() < 300:
                self._refresh()
            return self._tokens['access_token']

    # ── GraphQL ───────────────────────────────────────────────────────────────
    def _post(self, query, variables):
        def call():
            return requests.post(
                GRAPHQL_URL,
                headers={'Authorization': f'Bearer {self._access_token()}',
                         'Content-Type': 'application/json'},
                json={'query': query, 'variables': variables},
                timeout=30,
            )
        resp = call()
        if resp.status_code == 401:
            with self._lock:
                self._refresh()
            resp = call()
        if resp.status_code == 401:
            raise UpworkAuthError(f"Unauthorized: {resp.text[:300]}")
        resp.raise_for_status()
        return resp.json()

    def search(self, query='', category_ids=None, limit=50):
        """Return newest job postings (list of node dicts), newest first."""
        flt = {'pagination_eq': {'after': '0', 'first': limit}}
        if query:
            flt['searchExpression_eq'] = query
        if category_ids:
            flt['categoryIds_any'] = list(category_ids)
        variables = {'filter': flt, 'searchType': 'USER_JOBS_SEARCH',
                     'sort': [{'field': 'RECENCY'}]}

        data = self._post(SEARCH_QUERY % self._fields, variables)
        if data.get('errors') and self._fields is FULL_FIELDS and not data.get('data'):
            log.warning('Full field set rejected, falling back to minimal: %s',
                        json.dumps(data['errors'])[:400])
            self._fields = MIN_FIELDS
            data = self._post(SEARCH_QUERY % self._fields, variables)

        if data.get('errors') and not (data.get('data') or {}).get('marketplaceJobPostingsSearch'):
            msg = json.dumps(data['errors'], ensure_ascii=False)[:500]
            if 'scope' in msg.lower() or 'permission' in msg.lower():
                raise UpworkAuthError(f"API key lacks job-search scope: {msg}")
            raise RuntimeError(f"Upwork GraphQL error: {msg}")

        result = (data.get('data') or {}).get('marketplaceJobPostingsSearch') or {}
        return [e['node'] for e in result.get('edges') or [] if e.get('node')]
