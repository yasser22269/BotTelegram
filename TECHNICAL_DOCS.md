# 📚 التوثيق التقني - بوت مستقل

## نظرة عامة على البنية

```
┌─────────────────────────────────────────────────────┐
│           Telegram Bot Interface                    │
│  (python-telegram-bot library)                      │
└──────────────────┬──────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────────┐ ┌──▼──────────┐ ┌─▼──────────┐
│  Command   │ │  Message    │ │  Callback  │
│  Handlers  │ │  Handlers   │ │  Handlers  │
└───┬────────┘ └──┬──────────┘ └─┬──────────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
         ┌─────────▼─────────┐
         │   Bot Core        │
         │  (bot.py)         │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────────┐ ┌──▼──────────┐ ┌─▼──────────┐
│  Database  │ │  Scraper    │ │ Scheduler  │
│(database.py) │(advanced_   │ │(asyncio)   │
│             │ scraper.py)  │ │            │
└────────────┘ └─────────────┘ └────────────┘
```

---

## 📁 الملفات الرئيسية

### `bot.py` - البوت الرئيسي
**الوظيفة:** معالج الأوامر والرسائل

**الوظائف الرئيسية:**
- `start()` - بدء المحادثة مع المستخدم
- `handle_category_selection()` - معالجة اختيار التصنيفات
- `categories_command()` - تعديل التصنيفات
- `stop_command()` - إيقاف المتابعة
- `scrape_new_projects()` - مهمة دورية لفحص المشاريع

### `database.py` - إدارة قاعدة البيانات
**الوظيفة:** تخزين ومعالجة البيانات

**الجداول:**
- `users` - بيانات المستخدمين والتصنيفات
- `sent_projects` - المشاريع التي تم إرسالها
- `last_check` - آخر فحص لكل تصنيف

**الوظائف:**
```python
add_user(user_id, username, categories)
get_user_categories(user_id)
save_sent_project(...)
get_all_active_users()
deactivate_user(user_id)
```

### `advanced_scraper.py` - مراقب المشاريع
**الوظيفة:** جلب بيانات المشاريع من موقع مستقل

**الفئة:** `MustaqbalScraper`
```python
get_projects_by_category(category_id, limit)
get_new_projects(category_id)  # جديد فقط
```

### `config.py` - الإعدادات المركزية
**الوظيفة:** توحيد جميع الإعدادات والثوابت

### `database.py` - السجلات والرسائل
**الوظيفة:** تنسيق الرسائل المرسلة

---

## 🔄 مسار العمل

### 1. بدء البوت
```
/start command
    ↓
user → choose categories
    ↓
✅ Confirm
    ↓
save in database
    ↓
start monitoring
```

### 2. مراقبة المشاريع (دوري)
```
Timer (كل 5 دقائق)
    ↓
for each active user:
    ├─ get user categories
    └─ for each category:
        ├─ scrape projects
        ├─ filter new ones
        └─ send to user
```

### 3. بيانات المشروع
```python
{
    'id': 'unique_project_id',
    'title': 'عنوان المشروع',
    'description': 'وصف المشروع',
    'budget': 'الميزانية',
    'level': 'مستوى المشروع',
    'url': 'رابط المشروع',
    'category_id': 'معرف التصنيف',
    'posted_date': 'تاريخ النشر',
    'fetched_at': 'وقت الجلب'
}
```

---

## 🗄️ هيكل قاعدة البيانات

### جدول `users`
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    categories TEXT,        -- JSON array
    created_at TIMESTAMP,
    is_active INTEGER
);
```

### جدول `sent_projects`
```sql
CREATE TABLE sent_projects (
    project_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    category TEXT,
    url TEXT,
    sent_at TIMESTAMP,
    user_id INTEGER
);
```

### جدول `last_check`
```sql
CREATE TABLE last_check (
    category TEXT PRIMARY KEY,
    last_project_id TEXT,
    last_check_time TIMESTAMP
);
```

---

## 🔐 الأمان

### حماية البيانات الحساسة
- ✅ استخدام `.env` لتخزين التوكنات
- ✅ عدم الكشف عن بيانات المستخدمين
- ✅ حماية معرف الإدمن

### معالجة الأخطاء
- ✅ try-except في جميع العمليات
- ✅ تسجيل الأخطاء (logging)
- ✅ رسائل خطأ واضحة

---

## 📊 الإحصائيات

### عداد المستخدمين
```python
users = db.get_all_active_users()
total_users = len(users)
```

### المشاريع المرسلة
```python
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM sent_projects')
total_projects = cursor.fetchone()[0]
```

---

## 🚀 التطوير المستقبلي

### المميزات المخطط لها
- [ ] **فلاتر متقدمة** (ميزانية، مستوى، كلمات مفتاحية)
- [ ] **إحصائيات** (عدد المشاريع، الإحصائيات اليومية)
- [ ] **تنبيهات مخصصة** (أصوات مختلفة لتصنيفات مختلفة)
- [ ] **واجهة ويب** (لإدارة البوت)
- [ ] **دعم لغات متعددة** (عربي، إنجليزي)
- [ ] **ربط بقواعد بيانات خارجية**

### تحسينات الأداء
- [ ] **Caching** للبيانات المتكررة
- [ ] **Async/Await** محسّنة
- [ ] **معالجة دفعات** من الطلبات

---

## 🧪 الاختبار

### اختبار الأجزاء الفردية
```bash
python test_bot.py
```

### اختبار الـ Scraper
```python
from advanced_scraper import MustaqbalScraper

scraper = MustaqbalScraper()
projects = scraper.get_projects_by_category("1", limit=5)
print(projects)
```

### اختبار قاعدة البيانات
```python
from database import Database

db = Database()
db.add_user(123, "test", ["1", "2"])
print(db.get_user_categories(123))
```

---

## 📝 أمثلة الاستخدام

### إضافة مستخدم جديد
```python
db.add_user(
    user_id=123456789,
    username="ahmad",
    categories=["1", "2", "3"]  # البرمجة، الهاتف، التصميم
)
```

### جلب مشاريع جديدة
```python
scraper = MustaqbalScraper()
new_projects = scraper.get_new_projects("1")
for project in new_projects:
    print(f"{project['title']} - {project['budget']}")
```

### إرسال رسالة للمستخدم
```python
await context.bot.send_message(
    chat_id=user_id,
    text="رسالة المشروع",
    parse_mode='HTML'
)
```

---

## 🔗 المراجع

- [python-telegram-bot documentation](https://python-telegram-bot.readthedocs.io/)
- [APScheduler documentation](https://apscheduler.readthedocs.io/)
- [BeautifulSoup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests documentation](https://requests.readthedocs.io/)

---

**آخر تحديث:** 2026-04-25

