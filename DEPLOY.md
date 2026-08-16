# النشر على السيرفر (Hostinger shared hosting)

البوت يعمل 24/7 على `147.79.103.51` تحت المستخدم `u321534789`.

## المسارات

| العنصر | المسار |
|---|---|
| مجلد التطبيق | `~/bots/mustaqbal-bot/` |
| السكربت المُشغَّل | `bot_working.py` |
| البيئة الافتراضية | `~/bots/mustaqbal-bot/venv/` (Python 3.11 من `/opt/alt/python311`) |
| السجلات | `~/bots/mustaqbal-bot/logs/out-0.log` و `err-0.log` |
| بيانات المشتركين | `~/bots/mustaqbal-bot/users_data.json` |

## طبقات الاستمرارية

1. **PM2** — يعيد التشغيل فوراً لو البوت وقع أو تجاوز 250MB.
2. **`keepalive.sh`** — يرجّع البوت حتى لو الـ PM2 daemon نفسه مات.
3. **`watchdog.sh`** — حلقة منفصلة تنادي `keepalive.sh` كل 60 ثانية.
4. **cron من hPanel** — الطبقة الوحيدة اللي بتنجو من إعادة تشغيل السيرفر.

> السيرفر shared hosting: مفيش `systemd` ولا `crontab` CLI، والكتابة المباشرة في
> `/var/spool/cron/` لا يقرأها الـ daemon (تم اختبارها). لذلك الـ cron لازم من hPanel.

### إضافة الـ cron (مطلوبة مرة واحدة)

hPanel → Advanced → Cron Jobs، كل 5 دقائق:

```
/home/u321534789/bots/mustaqbal-bot/keepalive.sh
```

## أوامر الإدارة

```bash
ssh -p 65002 u321534789@147.79.103.51
source ~/.nvm/nvm.sh

pm2 list                          # الحالة
pm2 logs mustaqbal-bot            # السجلات المباشرة
pm2 restart mustaqbal-bot         # إعادة تشغيل
pm2 stop mustaqbal-bot            # إيقاف مؤقت
```

## تحديث الكود

```bash
scp -P 65002 bot_working.py u321534789@147.79.103.51:bots/mustaqbal-bot/
ssh -p 65002 u321534789@147.79.103.51 'source ~/.nvm/nvm.sh; pm2 restart mustaqbal-bot'
```

## تنبيه: نسخة واحدة فقط

Telegram long-polling يرجّع خطأ 409 لو اتنين بيستخدموا نفس التوكن. قبل ما تشغّل
البوت محلياً أو على Railway، أوقف نسخة السيرفر الأول.
