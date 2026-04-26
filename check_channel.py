#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من صلاحيات البوت في قناة Freelancer
Bot Permissions Checker for Freelancer Channel
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

# تحميل الإعدادات
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
FREELANCER_CHANNEL_ID = int(os.getenv('FREELANCER_CHANNEL_ID', '-1003559557908'))


async def check_channel_permissions():
    """التحقق من صلاحيات البوت في القناة"""
    print("\n" + "="*60)
    print("🔍 التحقق من صلاحيات البوت في القناة")
    print("="*60 + "\n")

    if not TELEGRAM_TOKEN:
        print("❌ خطأ: TELEGRAM_TOKEN غير محدد في ملف .env")
        return False

    try:
        bot = Bot(token=TELEGRAM_TOKEN)

        print(f"📋 معرف القناة: {FREELANCER_CHANNEL_ID}")
        print("⏳ جاري التحقق...")

        # الحصول على معلومات القناة
        try:
            chat = await bot.get_chat(FREELANCER_CHANNEL_ID)
            print(f"\n✅ تم الاتصال بالقناة بنجاح!")
            print(f"   📌 اسم القناة: {chat.title}")
            print(f"   📝 الوصف: {chat.description or 'بدون وصف'}")
            print(f"   👥 عدد الأعضاء: {chat.get_member_count() or 'غير معروف'}")
        except Exception as e:
            print(f"\n❌ خطأ في الاتصال بالقناة: {e}")
            return False

        # التحقق من صلاحيات البوت
        try:
            bot_member = await bot.get_chat_member(FREELANCER_CHANNEL_ID, bot.id)

            print(f"\n🔐 صلاحيات البوت في القناة:")
            print(f"   📍 دور البوت: {bot_member.status}")

            if bot_member.status == 'administrator':
                print(f"   ✅ البوت مسؤول في القناة")

                # معلومات الصلاحيات
                if hasattr(bot_member, 'can_send_messages'):
                    print(f"   {'✅' if bot_member.can_send_messages else '❌'} إرسال رسائل")
                if hasattr(bot_member, 'can_edit_messages'):
                    print(f"   {'✅' if bot_member.can_edit_messages else '❌'} تعديل الرسائل")
                if hasattr(bot_member, 'can_delete_messages'):
                    print(f"   {'✅' if bot_member.can_delete_messages else '❌'} حذف الرسائل")
                if hasattr(bot_member, 'can_pin_messages'):
                    print(f"   {'✅' if bot_member.can_pin_messages else '❌'} تثبيت الرسائل")

                return True

            elif bot_member.status == 'member':
                print(f"   ⚠️  البوت عضو عادي في القناة")
                print(f"   💡 قد يحتاج إلى صلاحيات إضافية")
                return True

            else:
                print(f"   ❌ البوت ليس عضواً في القناة")
                return False

        except Exception as e:
            print(f"\n❌ خطأ في الحصول على معلومات البوت: {e}")
            return False

    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        return False


async def test_send_message():
    """محاولة إرسال رسالة اختبار للقناة"""
    print("\n" + "-"*60)
    print("🧪 اختبار إرسال رسالة للقناة...")
    print("-"*60 + "\n")

    try:
        bot = Bot(token=TELEGRAM_TOKEN)

        test_message = "✅ اختبار الاتصال - البوت يعمل بشكل صحيح!"

        message = await bot.send_message(
            chat_id=FREELANCER_CHANNEL_ID,
            text=test_message
        )

        print(f"✅ تم إرسال الرسالة بنجاح!")
        print(f"   📍 معرف الرسالة: {message.message_id}")
        print(f"   ⏰ الوقت: {message.date}")

        return True

    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة: {e}")
        return False


async def main():
    """تشغيل الفحص"""
    perms_ok = await check_channel_permissions()

    if perms_ok:
        print("\n" + "="*60)
        print("🟢 البوت جاهز للعمل مع القناة!")
        print("="*60)
        print("\nهل تريد اختبار إرسال رسالة؟")
        print("اكتب 'y' للموافقة أو أي شيء آخر للإلغاء: ", end="")

        response = input().strip().lower()
        if response == 'y':
            test_ok = await test_send_message()
            if test_ok:
                print("\n✅ البوت يعمل بشكل مثالي!")
                sys.exit(0)
            else:
                print("\n⚠️  هناك مشكلة في الإرسال")
                sys.exit(1)
    else:
        print("\n" + "="*60)
        print("❌ هناك مشكلة في الاتصال بالقناة")
        print("="*60)
        print("\n💡 الحلول الممكنة:")
        print("1. تأكد من أن معرف القناة صحيح")
        print("2. تأكد من أن البوت عضو في القناة")
        print("3. تأكد من أن البوت مسؤول في القناة")
        print("4. تأكد من التوكن صحيح")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  تم إيقاف الفحص")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        sys.exit(1)

