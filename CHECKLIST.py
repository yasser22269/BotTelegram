#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
قائمة التحقق - بوت مستقل
Checklist - Mustaqbal Bot
"""

CHECKLIST = {
    "المتطلبات الأساسية": {
        "Python 3.9+": False,
        "pip": False,
        "اتصال إنترنت": False,
    },

    "إعداد Telegram": {
        "إنشاء بوت من @BotFather": False,
        "نسخ TELEGRAM_TOKEN": False,
        "الحصول على ADMIN_ID من @userinfobot": False,
        "التأكد من اسم البوت": False,
    },

    "التثبيت": {
        "تحميل المشروع": False,
        "تثبيت المكتبات (pip install -r requirements.txt)": False,
        "إنشاء ملف .env من .env.example": False,
        "إدراج التوكن والمعرف في .env": False,
    },

    "الملفات الأساسية": {
        "bot.py": False,
        "database.py": False,
        "advanced_scraper.py": False,
        "config.py": False,
        "utils.py": False,
        "analytics.py": False,
    },

    "ملفات الإعدادات": {
        "requirements.txt": False,
        ".env.example": False,
        ".env (محمي من Git)": False,
        ".gitignore": False,
    },

    "الاختبار": {
        "اختبار database.py": False,
        "اختبار advanced_scraper.py": False,
        "اختبار config.py": False,
        "تشغيل test_bot.py": False,
    },

    "الشغيل": {
        "تشغيل bot.py": False,
        "اختبار /start في Telegram": False,
        "اختيار التصنيفات": False,
        "تأكيد الاختيار": False,
        "استقبال المشاريع الأولى": False,
    },

    "التوثيق": {
        "قراءة README.md": False,
        "قراءة QUICKSTART.md": False,
        "قراءة INSTALL.md": False,
        "قراءة USER_GUIDE.md": False,
        "قراءة TECHNICAL_DOCS.md": False,
    },

    "الأمان": {
        "عدم مشاركة .env في Git": False,
        "عدم مشاركة TELEGRAM_TOKEN": False,
        "حذف bot_data.db الشخصي قبل المشاركة": False,
        "استخدام .gitignore بشكل صحيح": False,
    },

    "الصيانة": {
        "تحديث المكتبات دورياً": False,
        "عمل backup لقاعدة البيانات": False,
        "مراجعة السجلات (logs)": False,
        "اختبار جميع الأوامر": False,
    }
}


def print_checklist():
    """طباعة قائمة التحقق"""
    print("\n" + "="*60)
    print("✅ قائمة التحقق - بوت مستقل")
    print("="*60 + "\n")

    total_items = 0
    completed = 0

    for category, items in CHECKLIST.items():
        print(f"\n📌 {category}")
        print("-" * 50)

        for item, status in items.items():
            total_items += 1
            status_icon = "✅" if status else "⬜"
            completed += 1 if status else 0
            print(f"  {status_icon} {item}")

    print("\n" + "="*60)
    print(f"📊 التقدم: {completed}/{total_items} ({int(completed/total_items*100)}%)")
    print("="*60 + "\n")


def get_next_steps():
    """الحصول على الخطوات التالية"""
    incomplete = []

    for category, items in CHECKLIST.items():
        for item, status in items.items():
            if not status:
                incomplete.append(f"{category}: {item}")

    if incomplete:
        print("📋 الخطوات التالية:")
        for i, step in enumerate(incomplete[:5], 1):
            print(f"  {i}. {step}")
    else:
        print("🎉 تم إكمال جميع الخطوات!")


COMMANDS_REMINDER = """
📞 أوامر مهمة:

تثبيت المكتبات:
  pip install -r requirements.txt

تشغيل الاختبار:
  python test_bot.py

تشغيل البوت:
  python bot.py

على Windows:
  run_bot.bat

على Linux/Mac:
  ./run_bot.sh
"""


TROUBLESHOOTING = """
🆘 استكشاف الأخطاء:

خطأ: TELEGRAM_TOKEN غير محدد
  ✓ تأكد من وجود ملف .env
  ✓ تأكد من إدراج التوكن بشكل صحيح
  ✓ أعد تشغيل البوت

خطأ: No module named 'telegram'
  ✓ ثبّت المكتبات: pip install -r requirements.txt
  ✓ تأكد من استخدام Python الصحيح

خطأ: Database is locked
  ✓ تأكد من عدم تشغيل البوت مرتين
  ✓ احذف ملف .db وأعد التشغيل

البوت لا يرسل إشعارات
  ✓ تأكد من اختيار التصنيفات
  ✓ تأكد من الاتصال بالإنترنت
  ✓ تحقق من السجلات في console

الموقع لا يستجيب
  ✓ تأكد من الاتصال بالإنترنت
  ✓ جرّب تحديث advanced_scraper.py
  ✓ تحقق من حالة موقع مستقل
"""


RESOURCES = """
📚 الموارد المفيدة:

التوثيق الرسمي:
  🔗 python-telegram-bot: https://python-telegram-bot.readthedocs.io/
  🔗 APScheduler: https://apscheduler.readthedocs.io/
  🔗 BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/

المشروع:
  📁 المجلد: C:\\xampp\\htdocs\\BotTelegram
  📝 الملفات: README.md, INSTALL.md, USER_GUIDE.md

Telegram:
  🤖 @BotFather - لإنشاء البوتات
  🔍 @userinfobot - للحصول على معرّفك
"""


if __name__ == "__main__":
    import sys
    import os

    print(COMMANDS_REMINDER)
    print_checklist()
    get_next_steps()
    print(TROUBLESHOOTING)
    print(RESOURCES)

    print("\n" + "="*60)
    print("✨ شكراً لاستخدام بوت مستقل!")
    print("="*60 + "\n")

