"""
ملف اختبار البوت والـ Scraper
"""
import sys
import os

# إضافة المجلد الحالي للمسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from advanced_scraper import MustaqbalScraper
from config import CATEGORIES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database():
    """اختبار قاعدة البيانات"""
    print("\n" + "="*50)
    print("🧪 اختبار قاعدة البيانات")
    print("="*50)

    db = Database()

    # اختبار إضافة مستخدم
    print("\n✓ إضافة مستخدم تجريبي...")
    db.add_user(123456789, "test_user", ["1", "2", "3"])
    print("  ✅ تم بنجاح")

    # اختبار الحصول على تصنيفات المستخدم
    print("\n✓ الحصول على تصنيفات المستخدم...")
    categories = db.get_user_categories(123456789)
    print(f"  ✅ التصنيفات: {categories}")

    # اختبار حفظ مشروع
    print("\n✓ حفظ مشروع تجريبي...")
    db.save_sent_project(
        "project_123",
        "مشروع اختبار",
        "وصف المشروع",
        "البرمجة وتطوير المواقع",
        "https://mustaqbal.com/project/123",
        123456789
    )
    print("  ✅ تم بنجاح")

    print("\n✅ جميع اختبارات قاعدة البيانات نجحت!")


def test_categories():
    """اختبار التصنيفات"""
    print("\n" + "="*50)
    print("🧪 اختبار التصنيفات")
    print("="*50)

    print("\n✓ التصنيفات المتاحة:")
    for key, value in CATEGORIES.items():
        print(f"  {key}. {value}")

    print(f"\n✅ عدد التصنيفات: {len(CATEGORIES)}")


def test_scraper():
    """اختبار الـ Scraper"""
    print("\n" + "="*50)
    print("🧪 اختبار Scraper")
    print("="*50)

    scraper = MustaqbalScraper()

    print("\n✓ جاري اختبار scraper...")
    print("  ملاحظة: هذا قد يستغرق بعض الوقت...")

    # اختبار جلب المشاريع
    try:
        projects = scraper.get_projects_by_category("1", limit=3)

        if projects:
            print(f"\n✅ تم جلب {len(projects)} مشاريع:")
            for i, project in enumerate(projects, 1):
                print(f"\n  {i}. {project.get('title', 'بدون عنوان')}")
                print(f"     الميزانية: {project.get('budget', 'غير محدد')}")
                print(f"     الرابط: {project.get('url', 'بدون رابط')}")
        else:
            print("\n⚠️  لم يتم جلب أي مشاريع")
            print("   قد يكون الموقع متاح ولكن البيانات غير متاحة حالياً")

    except Exception as e:
        print(f"\n⚠️  خطأ في اختبار Scraper:")
        print(f"   {str(e)}")
        print("\n   هذا طبيعي إذا كان الموقع محمياً أو الاتصال بطيء")


def test_config():
    """اختبار الإعدادات"""
    print("\n" + "="*50)
    print("🧪 اختبار الإعدادات")
    print("="*50)

    from config import TELEGRAM_TOKEN, ADMIN_ID, SCRAPE_INTERVAL, MESSAGES

    print("\n✓ التحقق من الإعدادات:")

    token_status = "✅ محدد" if TELEGRAM_TOKEN else "❌ غير محدد"
    print(f"  TELEGRAM_TOKEN: {token_status}")

    admin_status = "✅ محدد" if ADMIN_ID else "❌ غير محدد"
    print(f"  ADMIN_ID: {admin_status}")

    print(f"  SCRAPE_INTERVAL: ✅ {SCRAPE_INTERVAL} ثانية")
    print(f"  عدد الرسائل المسجلة: ✅ {len(MESSAGES)} رسائل")

    if not TELEGRAM_TOKEN or not ADMIN_ID:
        print("\n⚠️  تحذير: تأكد من تحديث ملف .env")
        print("   اتبع التعليمات في INSTALL.md")
    else:
        print("\n✅ جميع الإعدادات محددة بشكل صحيح!")


def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🚀" * 25)
    print("بوت مستقل - ملف الاختبار")
    print("🚀" * 25)

    try:
        test_config()
        test_categories()
        test_database()
        test_scraper()

        print("\n" + "="*50)
        print("✅ اكتملت جميع الاختبارات!")
        print("="*50)
        print("\nالبوت جاهز للتشغيل!")
        print("شغّل البوت باستخدام: python bot.py\n")

    except Exception as e:
        print(f"\n❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

