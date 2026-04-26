#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
بوت مستقل - النسخة الخفيفة جداً
Mustaqbal Bot - Ultra Light Version
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.utils.request import Request
import time

# تحميل الإعدادات
load_dotenv()

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الثوابت
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
FREELANCER_CHANNEL_ID = int(os.getenv('FREELANCER_CHANNEL_ID', '-1003559557908'))

# التصنيفات
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

# تخزين البيانات
user_data = {}
last_update_id = 0


def send_welcome(bot, chat_id, first_name):
    """إرسال رسالة الترحيب"""
    welcome = f"""مرحباً {first_name} 👋

أنا بوت مستقل 🚀
أساعدك في متابعة المشاريع الجديدة

اختر التصنيفات:"""

    keyboard = []
    for key, value in CATEGORIES.items():
        keyboard.append([f"{key}. {value}"])
    keyboard.append(["✅ تأكيد"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    bot.send_message(chat_id=chat_id, text=welcome, reply_markup=reply_markup)


def handle_update(bot, update):
    """معالجة التحديثات"""
    global last_update_id

    if not update.get('message'):
        return

    message = update['message']
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    user_first_name = message['from'].get('first_name', 'صديقي')
    text = message.get('text', '').strip()

    if user_id not in user_data:
        user_data[user_id] = {'selected': []}

    # أمر البداية
    if text == '/start':
        send_welcome(bot, chat_id, user_first_name)
        logger.info(f"✅ المستخدم {user_id} ({user_first_name}) بدأ")
        return

    # أمر الإيقاف
    if text == '/stop':
        if user_id in user_data:
            del user_data[user_id]
        bot.send_message(chat_id=chat_id, text="👋 تم!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"👋 المستخدم {user_id} توقف")
        return

    # التأكيد
    if text == "✅ تأكيد":
        selected = user_data[user_id]['selected']
        if not selected:
            bot.send_message(chat_id=chat_id, text="⚠️ اختر تصنيف!")
            return

        cats = '\n'.join([f"• {CATEGORIES[c]}" for c in selected])
        msg = f"✅ تم!\n\nالمختار ({len(selected)}):\n{cats}\n\n/categories - تغيير\n/stop - إيقاف"
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=ReplyKeyboardRemove())
        logger.info(f"✅ تسجيل {user_id} مع {len(selected)} تصنيفات")
        return

    # اختيار تصنيف
    try:
        cat_num = text.split('.')[0].strip()
        if cat_num not in CATEGORIES:
            return

        selected = user_data[user_id]['selected']
        if cat_num in selected:
            selected.remove(cat_num)
            bot.send_message(chat_id=chat_id, text=f"❌ تم الحذف: {CATEGORIES[cat_num]}")
        else:
            selected.append(cat_num)
            bot.send_message(chat_id=chat_id, text=f"✅ تم الإضافة: {CATEGORIES[cat_num]}")

        cats = '\n'.join([f"• {CATEGORIES[c]}" for c in selected])
        bot.send_message(chat_id=chat_id, text=f"المختار ({len(selected)}):\n{cats}")

    except:
        pass


def main():
    """البداية"""
    global last_update_id

    if not TELEGRAM_TOKEN:
        print("❌ خطأ: TELEGRAM_TOKEN غير محدد!")
        return

    # إنشاء البوت
    request = Request(connect_timeout=15, read_timeout=15)
    bot = Bot(token=TELEGRAM_TOKEN, request=request)

    # اختبار الاتصال
    try:
        info = bot.get_me()
        print("\n" + "="*60)
        print("✅ البوت يعمل الآن!")
        print("="*60)
        print(f"🤖 البوت: @{info.username}")
        print(f"👤 المسؤول: @Elzero7")
        print(f"📢 القناة: Freelancer")
        print("="*60)
        print("\n💡 اختبر الآن على Telegram:")
        print(f"   https://t.me/{info.username}")
        print("\n⏳ في انتظار الرسائل...\n")
        print("="*60 + "\n")
        logger.info(f"✅ اتصال البوت نجح: @{info.username}")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return

    # الحلقة الرئيسية
    try:
        while True:
            updates = bot.get_updates(offset=last_update_id + 1, timeout=30)
            if updates:
                for update in updates:
                    last_update_id = update['update_id']
                    handle_update(bot, update)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n👋 توقف البوت")
        logger.info("👋 توقف البوت")
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        print(f"❌ خطأ: {e}")


if __name__ == '__main__':
    main()

