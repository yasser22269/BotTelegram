// Cloudflare Worker: fetches Mostaql pages for the bot, because Mostaql blocks the Hostinger IP.
// Settings → Variables: add secret RELAY_KEY (same value as MOSTAQL_RELAY_KEY in the bot's .env).
export default {
  async fetch(request, env) {
    if (!env.RELAY_KEY || request.headers.get('X-Relay-Key') !== env.RELAY_KEY) {
      return new Response('Unauthorized', { status: 401 });
    }
    let target;
    try {
      target = new URL(new URL(request.url).searchParams.get('url'));
    } catch {
      return new Response('Bad url', { status: 400 });
    }
    // Only Mostaql, so the worker can never be used as an open proxy.
    if (target.protocol !== 'https:' || target.hostname !== 'mostaql.com') {
      return new Response('Forbidden host', { status: 403 });
    }
    const upstream = await fetch(target, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
          + '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'ar,en-US;q=0.9',
      },
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { 'Content-Type': upstream.headers.get('Content-Type') || 'text/html; charset=utf-8' },
    });
  },
};
