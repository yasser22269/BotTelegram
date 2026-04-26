# 📦 ملخص المشروع - بوت مستقل

## 🎯 الهدف من المشروع

إنشاء بوت ذكي لتطبيق تيليجرام يقوم بمراقبة المشاريع الجديدة على موقع **مستقل** والإشعار بها فوراً.

---

## 📁 محتويات المشروع

### الملفات الأساسية:

```
C:\xampp\htdocs\BotTelegram/
│
├── 🤖 bot.py                    # البوت الرئيسي
├── 📊 database.py               # إدارة قاعدة البيانات
├── 🔍 advanced_scraper.py       # مراقب المشاريع
├── ⚙️  config.py                # الإعدادات المركزية
├── 🛠️  utils.py                 # دوال مساعدة
├── 📈 analytics.py              # الإحصائيات والمراقبة
│
├── 📝 requirements.txt           # المتطلبات
├── .env.example                # ملف الإعدادات (نموذج)
├── .env                         # ملف الإعدادات (يجب إنشاؤه)
├── .gitignore                  # ملف تجاهل Git
│
├── 🚀 run_bot.bat              # تشغيل على Windows
├── 🚀 run_bot.sh               # تشغيل على Linux/Mac
├── 🧪 test_bot.py              # اختبار البوت
│
├── 📚 README.md                # دليل البوت
├── 📖 INSTALL.md               # دليل التثبيت
├── 👤 USER_GUIDE.md            # دليل المستخدم
├── 📋 TECHNICAL_DOCS.md        # التوثيق التقني
│
└── 📂 data/                     # مجلد البيانات
    └── bot_data.db             # قاعدة البيانات
```

---

## 🔧 المتطلبات

- **Python 3.9+**
- **pip** (مدير الحزم)
- **توكن بوت من Telegram** (من @BotFather)
- **معرّف Telegram شخصي** (من @userinfobot)

---

## 📦 المكتبات المستخدمة

```
python-telegram-bot==20.0          # واجهة Telegram
beautifulsoup4==4.12.2             # Web Scraping
requests==2.31.0                   # طلبات HTTP
selenium==4.15.0                   # للمحتوى الديناميكي
python-dotenv==1.0.0               # متغيرات البيئة
apscheduler==3.10.4                # مهام دورية
```

---

## ✨ المميزات المتوفرة

### 1️⃣ واجهة المستخدم
- ✅ قائمة تصنيفات تفاعلية
- ✅ أوامر بسيطة وسهلة
- ✅ رسائل واضحة ومفيدة

### 2️⃣ مراقبة المشاريع
- ✅ فحص دوري (كل 5 دقائق)
- ✅ كشف المشاريع الجديدة فقط
- ✅ إرسال فوري للمستخدمين

### 3️⃣ إدارة البيانات
- ✅ قاعدة بيانات SQLite
- ✅ حفظ بيانات المستخدمين
- ✅ تتبع المشاريع المرسلة

### 4️⃣ الإحصائيات والمراقبة
- ✅ إحصائيات الاستخدام
- ✅ مراقبة صحة النظام
- ✅ تقارير مفصلة

### 5️⃣ الأمان
- ✅ حماية متغيرات البيئة
- ✅ معالجة أخطاء محسّنة
- ✅ سجلات مفصلة

---

## 🚀 خطوات الاستخدام

### 1. التثبيت
```bash
cd C:\xampp\htdocs\BotTelegram
pip install -r requirements.txt
```

### 2. الإعداد
```bash
# انسخ ملف الإعدادات
copy .env.example .env

# ثم عدّل .env وأضف:
# TELEGRAM_TOKEN=your_token
# ADMIN_ID=your_id
```

### 3. الاختبار
```bash
python test_bot.py
```

### 4. التشغيل
```bash
# على Windows
run_bot.bat

# أو على Linux/Mac
./run_bot.sh

# أو مباشرة
python bot.py
```

---

## 📊 هيكل البيانات

### جدول المستخدمين
```
user_id (INTEGER) - معرف المستخدم
username (TEXT) - اسم المستخدم
categories (TEXT) - التصنيفات (JSON)
created_at (TIMESTAMP) - تاريخ الإنضمام
is_active (INTEGER) - حالة النشاط
```

### جدول المشاريع المرسلة
```
project_id (TEXT) - معرف المشروع
title (TEXT) - العنوان
description (TEXT) - الوصف
category (TEXT) - التصنيف
url (TEXT) - رابط المشروع
sent_at (TIMESTAMP) - وقت الإرسال
user_id (INTEGER) - معرف المستخدم
```

---

## 🔄 دورة عمل البوت

```
1. المستخدم يبدأ البوت
   ↓
2. يختار التصنيفات المطلوبة
   ↓
3. يتم حفظ البيانات في قاعدة البيانات
   ↓
4. البوت يبدأ المراقبة الدورية
   ↓
5. كل 5 دقائق:
   - فحص التصنيفات المختارة
   - كشف المشاريع الجديدة
   - إرسال الإشعارات للمستخدمين
```

---

## 📞 الأوامر المتاحة

| الأمر | الوصف |
|------|-------|
| `/start` | بدء البوت واختيار التصنيفات |
| `/categories` | تعديل التصنيفات |
| `/stop` | إيقاف المتابعة |

---

## 🧪 الاختبار

### اختبار شامل
```bash
python test_bot.py
```

### اختبار الأجزاء الفردية
```python
# اختبار Scraper
from advanced_scraper import MustaqbalScraper
scraper = MustaqbalScraper()
projects = scraper.get_projects_by_category("1")

# اختبار Database
from database import Database
db = Database()
db.add_user(123, "test", ["1", "2"])

# اختبار Analytics
from analytics import Analytics
analytics = Analytics()
print(analytics.get_statistics_report())
```

---

## 📚 الملفات الموثقة

1. **README.md** - نظرة عامة وسريعة
2. **INSTALL.md** - دليل التثبيت والإعداد
3. **USER_GUIDE.md** - دليل المستخدم
4. **TECHNICAL_DOCS.md** - التوثيق التقني المفصل

---

## 🎯 التطوير المستقبلي

### المميزات المخطط إضافتها:
- [ ] فلاتر متقدمة (ميزانية، مستوى)
- [ ] نظام تقييم وحفظ المفضلة
- [ ] إحصائيات تفصيلية
- [ ] واجهة ويب للإدارة
- [ ] دعم لغات متعددة
- [ ] نظام تنبيهات مخصص
- [ ] تكامل مع API مستقل

### تحسينات الأداء:
- [ ] Caching للبيانات
- [ ] معالجة دفعات
- [ ] تحسين الـ Scraping

---

## ⚙️ الإعدادات القابلة للتخصيص

في ملف `.env`:
```
TELEGRAM_TOKEN          # توكن البوت
ADMIN_ID                # معرف الإدمن
SCRAPE_INTERVAL         # فترة الفحص بالثواني
MUSTAQBAL_BASE_URL      # رابط الموقع
DATABASE_PATH           # مسار قاعدة البيانات
```

---

## 🔐 ملاحظات الأمان

✅ **استخدم متغيرات البيئة** لحفظ الأسرار
✅ **لا تشارك ملف `.env`** في Git
✅ **استخدم `.gitignore`** لحماية البيانات الحساسة
✅ **تحديث المتطلبات** بانتظام

---

## 📈 الإحصائيات

البوت يتابع:
- 📊 عدد المستخدمين النشطين
- 📝 عدد المشاريع المرسلة
- 🏆 أكثر التصنيفات نشاطاً
- 📅 المشاريع المرسلة يومياً

---

## 🆘 استكشاف الأخطاء

### الخطأ: TELEGRAM_TOKEN غير محدد
```bash
# تأكد من إنشاء ملف .env
copy .env.example .env
# ثم عدّل الملف وأضف التوكن
```

### الخطأ: No module named 'telegram'
```bash
pip install python-telegram-bot==20.0
```

### الخطأ: Database is locked
```
تأكد من عدم تشغيل البوت مرتين في نفس الوقت
```

---

## 📖 المراجع والموارد

- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Requests](https://requests.readthedocs.io/)
- [SQLite](https://www.sqlite.org/docs.html)

---

## 📜 الترخيص

هذا المشروع مفتوح المصدر وحر الاستخدام.

---

## 👨‍💻 المساهمة

نرحب بأي مساهمات أو اقتراحات لتحسين البوت!

---

**تم إنشاء البوت بنجاح! ✅**

*آخر تحديث: 2026-04-25*

