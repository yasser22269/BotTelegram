"""
ملف إعدادات البوت المركزي
"""
import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات تيليجرام
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
ADMIN_ID = os.getenv('ADMIN_ID', '')

# إعدادات المراقبة
SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', 300))  # بالثواني
CHECK_TIMEOUT = 10  # timeout للطلبات

# إعدادات قاعدة البيانات
DATABASE_PATH = os.getenv('DATABASE_PATH', './data/bot_data.db')

# إعدادات مستقل
MUSTAQBAL_BASE_URL = os.getenv('MUSTAQBAL_BASE_URL', 'https://www.mustaqbal.com')

# إعدادات القنوات
FREELANCER_CHANNEL_ID = int(os.getenv('FREELANCER_CHANNEL_ID', '-1003559557908'))
SEND_TO_CHANNEL = os.getenv('SEND_TO_CHANNEL', 'true').lower() == 'true'

# تصنيفات مستقل
CATEGORIES = {
    "1": "البرمجة وتطوير المواقع",
    "2": "تطوير تطبيقات الهاتف",
    "3": "التصميم والوسائط المتعددة",
    "4": "التسويق الرقمي",
    "5": "الكتابة والترجمة",
    "6": "البيانات والإحصائيات",
    "7": "الإدارة والاستشارات",
    "8": "الصوت والموسيقى",
    "9": "الفيديو والمونتاج",
    "10": "التدريس والتعليم الأكاديمي",
}

# رسائل البوت
MESSAGES = {
    'welcome': """
مرحباً {first_name} 👋

أنا بوت مستقل - أساعدك في متابعة المشاريع الجديدة على منصة مستقل 🚀

سأرسل لك المشاريع الجديدة فور نزولها في التصنيفات التي تختارها.

اختر التصنيفات التي تهمك:
    """,

    'confirm_categories': """
✅ تم تسجيلك بنجاح!

ستتابع التصنيفات التالية:
{categories}

سأرسل لك المشاريع الجديدة فور نزولها 🔔

الأوامر المتاحة:
/categories - تغيير التصنيفات
/stop - إيقاف المتابعة
    """,

    'new_project': """
🎯 مشروع جديد!

📌 {title}

📝 {description}

💰 الميزانية: {budget}

🏆 المستوى: {level}

📅 التاريخ: {date}

🔗 الرابط: {url}
    """,
}

# إعدادات السجلات
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

