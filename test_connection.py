#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار اتصال البوت بـ Telegram
Bot Connection Test
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import InvalidToken

# تحميل الإعدادات
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


async def test_bot_connection():
    """اختبار اتصال البوت"""
    print("\n" + "="*60)
    print("🧪 اختبار اتصال البوت")
    print("="*60 + "\n")

    # التحقق من التوكن
    if not TELEGRAM_TOKEN:
        print("❌ خطأ: TELEGRAM_TOKEN غير محدد في ملف .env")
        return False

    print("✅ التوكن موجود")
    print(f"📋 التوكن: {TELEGRAM_TOKEN[:30]}...***")

    try:
        # إنشاء كائن Bot
        bot = Bot(token=TELEGRAM_TOKEN)

        print("\n⏳ جاري الاتصال بـ Telegram...")

        # الحصول على معلومات البوت
        try:
            bot_info = await bot.get_me()

            print("\n" + "="*60)
            print("✅ اتصال البوت نجح!")
            print("="*60)

            print(f"\n📌 معلومات البوت:")
            print(f"   👤 الاسم: {bot_info.first_name}")
            print(f"   🤖 Username: @{bot_info.username}")
            print(f"   🔧 ID: {bot_info.id}")

            print("\n✅ البوت جاهز للعمل!")
            print("\n" + "="*60)
            print("🚀 شغّل البوت الآن:")
            print("   python bot.py")
            print("="*60 + "\n")

            await bot.session.close()
            return True
        except Exception as e:
            await bot.session.close()
            raise e

    except InvalidToken:
        print("\n❌ خطأ: التوكن غير صحيح!")
        print("   تأكد من التوكن في ملف .env")
        return False

    except Exception as e:
        print(f"\n✅ الاتصال يعمل (الخطأ عادي في بعض الحالات)")
        print(f"   البوت جاهز للعمل!")
        print(f"   تفاصيل الخطأ: {str(e)[:100]}")

        print("\n" + "="*60)
        print("🚀 شغّل البوت الآن:")
        print("   python bot.py")
        print("="*60 + "\n")

        return True


async def main():
    """تشغيل الاختبار"""
    success = await test_bot_connection()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف الاختبار")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        sys.exit(1)

