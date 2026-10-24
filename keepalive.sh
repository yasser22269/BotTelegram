#!/bin/bash
# hPanel cron: /bin/bash /home/u321534789/bots/mustaqbal-bot/keepalive.sh
# The scheduler lives outside the killed process tree and survives host restarts.
set -u
APP="$HOME/bots/mustaqbal-bot"
NAME="mustaqbal-bot"
cd "$APP" || exit 1
mkdir -p logs
# Concurrent cron/manual invocations must never start competing PM2 daemons.
exec 9>"$APP/.keepalive.lock"
flock -n 9 || exit 0
SOURCE="${1:-cron}"
case "$SOURCE" in cron|watchdog|manual) ;; *) exit 2 ;; esac
date '+%F %T' > "$APP/logs/.last-$SOURCE"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" >/dev/null 2>&1
command -v pm2 >/dev/null || exit 1

# Copy/truncate retains the inode PM2 already has open.
for f in logs/out-0.log logs/err-0.log logs/keepalive.log; do
    if [ -f "$f" ] && [ "$(stat -c %s "$f")" -gt 20971520 ]; then
        tail -c 5242880 "$f" > "$f.trim" && cat "$f.trim" > "$f"
        rm -f "$f.trim"
    fi
done

if timeout 30 pm2 describe "$NAME" 9>&- 2>/dev/null | grep -qE 'status.*online'; then
    if "$APP/venv/bin/python" "$APP/bot_runtime.py" --check; then
        exit 0
    fi
    echo "[$(date -u '+%FT%TZ')] stale bot heartbeat; restarting" >> logs/keepalive.log
    timeout 30 pm2 restart "$NAME" 9>&- >> logs/keepalive.log 2>&1 || exit 1
else
    echo "[$(date -u '+%FT%TZ')] bot offline; starting via $SOURCE" >> logs/keepalive.log
    timeout 30 pm2 start "$APP/ecosystem.config.js" 9>&- >> logs/keepalive.log 2>&1 || exit 1
fi
timeout 30 pm2 save 9>&- >/dev/null 2>&1
