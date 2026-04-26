"""
نظام المراقبة والإحصائيات
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


class Analytics:
    """تحليل الإحصائيات والبيانات"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    def get_total_users(self) -> int:
        """الحصول على عدد المستخدمين الكلي"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            result = cursor.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"خطأ في الحصول على عدد المستخدمين: {e}")
            return 0

    def get_total_projects_sent(self) -> int:
        """الحصول على عدد المشاريع المرسلة الكلي"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sent_projects')
            result = cursor.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"خطأ في الحصول على عدد المشاريع: {e}")
            return 0

    def get_projects_by_category(self) -> Dict[str, int]:
        """الحصول على عدد المشاريع حسب التصنيف"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT category, COUNT(*) as count FROM sent_projects GROUP BY category'
            )
            results = cursor.fetchall()
            conn.close()

            return {row[0]: row[1] for row in results}
        except Exception as e:
            logger.error(f"خطأ في الحصول على المشاريع حسب التصنيف: {e}")
            return {}

    def get_projects_today(self) -> int:
        """الحصول على عدد المشاريع المرسلة اليوم"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = datetime.now().date()
            cursor.execute(
                'SELECT COUNT(*) FROM sent_projects WHERE DATE(sent_at) = ?',
                (today,)
            )
            result = cursor.fetchone()[0]
            conn.close()
            return result
        except Exception as e:
            logger.error(f"خطأ في الحصول على مشاريع اليوم: {e}")
            return 0

    def get_most_active_categories(self, limit: int = 5) -> list:
        """الحصول على أكثر التصنيفات نشاطاً"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT category, COUNT(*) as count FROM sent_projects GROUP BY category ORDER BY count DESC LIMIT ?',
                (limit,)
            )
            results = cursor.fetchall()
            conn.close()

            return results
        except Exception as e:
            logger.error(f"خطأ في الحصول على التصنيفات النشطة: {e}")
            return []

    def get_user_stats(self, user_id: int) -> Dict:
        """الحصول على إحصائيات مستخدم معين"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # عدد المشاريع المستقبلة من قبل المستخدم
            cursor.execute(
                'SELECT COUNT(*) FROM sent_projects WHERE user_id = ?',
                (user_id,)
            )
            projects_count = cursor.fetchone()[0]

            # التصنيفات المختارة
            cursor.execute(
                'SELECT categories, created_at FROM users WHERE user_id = ?',
                (user_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                import json
                return {
                    'projects_received': projects_count,
                    'categories': json.loads(result[0]),
                    'joined_at': result[1]
                }

            return {}
        except Exception as e:
            logger.error(f"خطأ في الحصول على إحصائيات المستخدم: {e}")
            return {}

    def get_statistics_report(self) -> str:
        """الحصول على تقرير إحصائيات شامل"""
        try:
            total_users = self.get_total_users()
            total_projects = self.get_total_projects_sent()
            today_projects = self.get_projects_today()
            top_categories = self.get_most_active_categories(3)

            report = f"""
📊 <b>تقرير الإحصائيات</b>

👥 <b>إجمالي المستخدمين:</b> {total_users}
📝 <b>إجمالي المشاريع المرسلة:</b> {total_projects}
📅 <b>المشاريع المرسلة اليوم:</b> {today_projects}

🏆 <b>أكثر التصنيفات نشاطاً:</b>
            """

            for category, count in top_categories:
                report += f"\n• {category}: {count} مشروع"

            report += f"\n\n⏰ <b>التحديث:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            return report
        except Exception as e:
            logger.error(f"خطأ في إنشاء التقرير: {e}")
            return "❌ حدث خطأ في الحصول على التقرير"


class Monitoring:
    """مراقبة صحة البوت والأداء"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.start_time = datetime.now()

    def get_uptime(self) -> str:
        """الحصول على وقت التشغيل"""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours}h {minutes}m {seconds}s"

    def check_database_health(self) -> Dict:
        """فحص صحة قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # عد الجداول
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = cursor.fetchall()

            # حجم قاعدة البيانات
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

            conn.close()

            return {
                'status': 'healthy',
                'tables': len(tables),
                'size_mb': round(db_size / (1024 * 1024), 2),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"خطأ في فحص صحة قاعدة البيانات: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_health_report(self) -> str:
        """الحصول على تقرير صحة النظام"""
        health = self.check_database_health()
        uptime = self.get_uptime()

        status_emoji = "✅" if health['status'] == 'healthy' else "❌"

        report = f"""
{status_emoji} <b>تقرير صحة النظام</b>

🔧 <b>حالة قاعدة البيانات:</b> {health['status']}
⏱️  <b>وقت التشغيل:</b> {uptime}
💾 <b>حجم قاعدة البيانات:</b> {health.get('size_mb', 'غير معروف')} MB
📊 <b>عدد الجداول:</b> {health.get('tables', 'غير معروف')}

⏰ <b>آخر تحديث:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    analytics = Analytics()
    monitoring = Monitoring()

    print("إحصائيات البوت:")
    print(analytics.get_statistics_report())

    print("\n" + "="*50 + "\n")

    print("تقرير صحة النظام:")
    print(monitoring.get_health_report())

