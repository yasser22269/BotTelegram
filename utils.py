"""
دوال مساعدة عامة للبوت
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TextFormatter:
    """تنسيق النصوص والرسائل"""

    @staticmethod
    def format_project_message(project: Dict[str, Any]) -> str:
        """تنسيق رسالة المشروع"""
        message = f"""
🎯 <b>مشروع جديد!</b>

📌 <b>{project.get('title', 'بدون عنوان')}</b>

📝 <i>{project.get('description', '')[:200]}</i>

💰 <b>الميزانية:</b> {project.get('budget', 'غير محدد')}
🏆 <b>المستوى:</b> {project.get('level', 'غير محدد')}
📅 <b>التاريخ:</b> {project.get('posted_date', 'غير محدد')}

🔗 <a href="{project.get('url', '')}">اضغط هنا للمشروع</a>
        """
        return message.strip()

    @staticmethod
    def format_categories_list(categories: Dict[str, str]) -> str:
        """تنسيق قائمة التصنيفات"""
        text = "📋 <b>التصنيفات المتاحة:</b>\n\n"
        for key, value in categories.items():
            text += f"<b>{key}.</b> {value}\n"
        return text

    @staticmethod
    def format_user_stats(total_projects: int, total_users: int) -> str:
        """تنسيق إحصائيات المستخدمين"""
        message = f"""
📊 <b>إحصائيات البوت</b>

👥 <b>عدد المستخدمين:</b> {total_users}
📝 <b>عدد المشاريع المرسلة:</b> {total_projects}
📅 <b>التاريخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        return message.strip()


class DataValidator:
    """التحقق من صحة البيانات"""

    @staticmethod
    def validate_category_id(category_id: str, valid_categories: Dict) -> bool:
        """التحقق من صحة معرف التصنيف"""
        return category_id in valid_categories

    @staticmethod
    def validate_user_categories(categories: List[str], valid_categories: Dict) -> bool:
        """التحقق من صحة قائمة التصنيفات"""
        if not categories or not isinstance(categories, list):
            return False

        for cat in categories:
            if cat not in valid_categories:
                return False

        return True

    @staticmethod
    def validate_project_data(project: Dict[str, Any]) -> bool:
        """التحقق من صحة بيانات المشروع"""
        required_fields = ['id', 'title', 'url']

        for field in required_fields:
            if field not in project or not project[field]:
                return False

        return True


class RateLimiter:
    """تحديد معدل الرسائل"""

    def __init__(self, max_messages_per_minute: int = 30):
        self.max_messages = max_messages_per_minute
        self.message_timestamps = {}

    def is_allowed(self, user_id: int) -> bool:
        """التحقق من إمكانية إرسال رسالة للمستخدم"""
        now = datetime.now()

        if user_id not in self.message_timestamps:
            self.message_timestamps[user_id] = []

        # إزالة الرسائل القديمة (أكثر من دقيقة)
        self.message_timestamps[user_id] = [
            ts for ts in self.message_timestamps[user_id]
            if (now - ts).seconds < 60
        ]

        if len(self.message_timestamps[user_id]) < self.max_messages:
            self.message_timestamps[user_id].append(now)
            return True

        return False


class CacheManager:
    """إدارة ذاكرة التخزين المؤقت"""

    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    def set(self, key: str, value: Any) -> None:
        """حفظ قيمة في الذاكرة"""
        self.cache[key] = {
            'value': value,
            'timestamp': datetime.now()
        }

    def get(self, key: str) -> Any:
        """الحصول على قيمة من الذاكرة"""
        if key not in self.cache:
            return None

        item = self.cache[key]
        age = (datetime.now() - item['timestamp']).seconds

        if age > self.ttl:
            del self.cache[key]
            return None

        return item['value']

    def clear(self) -> None:
        """مسح الذاكرة"""
        self.cache.clear()


class FileManager:
    """إدارة الملفات"""

    @staticmethod
    def load_json(filepath: str) -> Dict:
        """تحميل ملف JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في تحميل {filepath}: {e}")
            return {}

    @staticmethod
    def save_json(filepath: str, data: Dict) -> bool:
        """حفظ ملف JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"خطأ في حفظ {filepath}: {e}")
            return False


class Logger:
    """نظام السجلات المحسّن"""

    @staticmethod
    def setup_logging(log_file: str = 'bot.log') -> logging.Logger:
        """إعداد نظام السجلات"""
        logger = logging.getLogger('MustaqbalBot')
        logger.setLevel(logging.INFO)

        # مسجل الملف
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # مسجل Console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # تنسيق السجلات
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger


# إنشاء كائنات عامة
text_formatter = TextFormatter()
data_validator = DataValidator()
rate_limiter = RateLimiter()
cache_manager = CacheManager()
file_manager = FileManager()


if __name__ == "__main__":
    # اختبار الأدوات
    project = {
        'title': 'مشروع اختبار',
        'description': 'وصف المشروع',
        'budget': '500 ريال',
        'level': 'متوسط',
        'posted_date': '2026-04-25',
        'url': 'https://mustaqbal.com/project/123',
        'id': '123'
    }

    print("اختبار TextFormatter:")
    print(text_formatter.format_project_message(project))
    print("\n" + "="*50 + "\n")

    print("اختبار DataValidator:")
    print(f"هل بيانات المشروع صحيحة؟ {data_validator.validate_project_data(project)}")

