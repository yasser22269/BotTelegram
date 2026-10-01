# Upwork Hunter 🎯

بوت تيليجرام شخصي بيبعتلك وظائف Upwork الجديدة أول بأول (زي Offers Hunter) بفلاترك أنت.
بيستخدم **Upwork API الرسمي** (GraphQL) — مفيش scraping.

## التشغيل لأول مرة

1. **بوت تيليجرام جديد**: من [@BotFather](https://t.me/BotFather) → `/newbot` → حط التوكن في `TELEGRAM_TOKEN` جوه `.env`.
   متستخدمش توكن بوت مستقل، لأن النسخة اللي على السيرفر هتعمل تعارض (خطأ 409).
2. **مفتاح Upwork**: من https://www.upwork.com/developer/keys
   - اتأكد إن الـ Callback URL مكتوب `http://localhost:8888` بالظبط
   - واتأكد إن المفتاح عليه صلاحية قراءة وظائف الماركت بليس (*Read marketplace Job Postings*)
3. نزّل المتطلبات وسجّل الدخول في Upwork مرة واحدة:
   ```
   pip install -r requirements.txt
   python auth.py
   ```
4. شغّل البوت:
   ```
   run.bat        (بيعيد التشغيل لوحده لو البوت وقع)
   ```
   أو `python bot.py`. بعد كده ابعت `/settings` للبوت.

## الأوامر

| الأمر | الوظيفة |
|---|---|
| `/settings` | الإعدادات والأزرار (إيقاف مؤقت، نوع الوظيفة، الدفع الموثّق، التصنيفات) |
| `/latest 5` | آخر N وظيفة مطابقة للفلاتر دلوقتي |
| `/status` | حالة البوت والاتصال بـ Upwork |
| `/addkw laravel OR php` / `/delkw 1` / `/clearkw` | جمل البحث، وكل جملة بتتبحث لوحدها |
| `/type all\|hourly\|fixed` | نوع التعاقد |
| `/minhourly 15` · `/minfixed 100` · `/minspent 500` | حد أدنى للسعر بالساعة، وللميزانية الثابتة، ولإنفاق العميل |
| `/verified on\|off` · `/nobudget on\|off` | الدفع الموثّق فقط، وإظهار الوظايف اللي من غير ميزانية |
| `/exc India` · `/exw wordpress` | استبعاد دولة أو كلمة (نفس الأمر بيضيفها ولو اتكرر بيشيلها) |
| `/interval 60` | عدد الثواني بين كل فحص والتاني (أقل حاجة 20) |

## ملاحظات

- الإعدادات بتتحفظ في `data/settings.json`، والتوكنز في `data/tokens.json`، والسجل في `data/bot.log`.
- الـ access token بيتجدد لوحده. الـ refresh token صلاحيته حوالي أسبوعين، فلو البوت فضل مقفول أكتر من كده شغّل `python auth.py` تاني.
- وأنت بتغيّر الفلاتر، البوت مش بيبعت وظايف أقدم من `MAX_JOB_AGE_MINUTES` (افتراضياً 60 دقيقة)، علشان ميغرقكش بوظايف قديمة.
