# 🤖 دليل التثبيت والتشغيل - بوت مستقل

## المتطلبات الأساسية

- **Python 3.9 أو أحدث**
- **pip** (مدير الحزم)
- **Windows / macOS / Linux**

---

## خطوات التثبيت

### الخطوة 1️⃣: إنشاء بوت على تيليجرام

1. افتح [BotFather](https://t.me/botfather) على تيليجرام
2. اكتب `/newbot` واتبع التعليمات
3. انسخ **Token** الذي يعطيك إياه

### الخطوة 2️⃣: الحصول على معرّف Telegram الخاص بك

1. افتح [IDBot](https://t.me/userinfobot)
2. اكتب `/start` وسيعطيك معرّفك

### الخطوة 3️⃣: تثبيت المتطلبات

```bash
# اذهب إلى مجلد البوت
cd C:\xampp\htdocs\BotTelegram

# ثبّت المتطلبات
pip install -r requirements.txt
```

### الخطوة 4️⃣: إعداد ملف .env

1. افتح `.env.example`
2. أنشئ ملف جديد باسم `.env`
3. أضف البيانات:

```env
TELEGRAM_TOKEN=your_token_from_botfather_here
ADMIN_ID=your_user_id_here
SCRAPE_INTERVAL=300
MUSTAQBAL_BASE_URL=https://www.mustaqbal.com
DATABASE_PATH=./data/bot_data.db
```

**مثال:**
```env
TELEGRAM_TOKEN=1234567890:ABCDefGHIjklmnoPQRstuvWXyz-ABCD-1234
ADMIN_ID=987654321
SCRAPE_INTERVAL=300
MUSTAQBAL_BASE_URL=https://www.mustaqbal.com
DATABASE_PATH=./data/bot_data.db
```

### الخطوة 5️⃣: تشغيل البوت

```bash
# على Windows
python bot.py

# أو إذا كان عندك Python 3
python3 bot.py
```

**إذا رأيت هذا الرسالة، فالبوت يعمل بنجاح:**
```
✅ تم بدء المهام الدورية
🚀 جاري بدء البوت...
```

---

## 🧪 اختبار البوت

1. ابحث عن بوتك على تيليجرام (الاسم الذي أعطيته له)
2. اضغط `/start`
3. اختر التصنيفات المطلوبة
4. اضغط "✅ تأكيد الاختيار"

---

## 📋 الأوامر المتاحة

| الأمر | الوصف |
|------|-------|
| `/start` | بدء البوت واختيار التصنيفات |
| `/categories` | تعديل التصنيفات |
| `/stop` | إيقاف المتابعة |

---

## 🔧 استكشاف الأخطاء

### خطأ: "TELEGRAM_TOKEN غير محدد"
- ✅ تأكد من إنشاء ملف `.env`
- ✅ تأكد من نسخ التوكن بشكل صحيح من BotFather

### خطأ: "No module named telegram"
```bash
pip install python-telegram-bot==20.0
```

### خطأ: "Database is locked"
- ✅ تأكد من عدم تشغيل البوت مرتين في نفس الوقت

### لا يصل البوت إلى مستقل
- ✅ تأكد من اتصالك بالإنترنت
- ✅ تأكد من أن الموقع متاح

---

## 📊 هيكل قاعدة البيانات

البوت ينشئ قاعدة بيانات SQLite تلقائياً:

```
data/
└── bot_data.db
    ├── users          (المستخدمون)
    ├── sent_projects  (المشاريع المرسلة)
    └── last_check     (آخر فحص)
```

---

## 🚀 نصائح متقدمة

### تشغيل البوت في الخلفية (Windows)

1. أنشئ ملف باسم `run_bot.bat`:
```batch
@echo off
cd C:\xampp\htdocs\BotTelegram
python bot.py
pause
```

2. اضغط مرتين على الملف لتشغيل البوت

### تشغيل البوت كخدمة

على Linux/macOS، يمكنك استخدام `systemd` أو `supervisor`

---

## 📞 الدعم والمساعدة

إذا واجهت مشاكل:

1. تحقق من رسائل الخطأ في الـ Console
2. تأكد من تثبيت جميع المتطلبات
3. تأكد من صحة ملف `.env`

---

**تم! البوت جاهز للاستخدام** ✅

