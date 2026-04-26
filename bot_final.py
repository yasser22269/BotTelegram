#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
بوت مستقل - النسخة الأخيرة
Mustaqbal Bot - Final Version
"""

import logging
import os
from dotenv import load_dotenv
from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.utils.request import Request

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
user_data_store = {}


def start(bot, update):
    """معالج أمر /start"""
    try:
        user = update.message.from_user
        user_id = user.id

        welcome_message = f"""مرحباً {user.first_name} 👋

أنا بوت مستقل - أساعدك في متابعة المشاريع الجديدة على منصة مستقل 🚀

اختر التصنيفات التي تهمك:"""

        # إنشاء لوحة المفاتيح
        keyboard = []
        for key, value in CATEGORIES.items():
            keyboard.append([f"{key}. {value}"])
        keyboard.append(["✅ تأكيد"])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        update.message.reply_text(welcome_message, reply_markup=reply_markup)

        # تهيئة البيانات
        user_data_store[user_id] = {'selected_categories': []}
        logger.info(f"✅ المستخدم {user_id} ({user.first_name}) بدأ البوت")

    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")


def handle_message(bot, update):
    """معالج الرسائل"""
    try:
        user = update.message.from_user
        user_id = user.id
        text = update.message.text

        if user_id not in user_data_store:
            user_data_store[user_id] = {'selected_categories': []}

        # معالج التأكيد
        if text == "✅ تأكيد":
            selected = user_data_store[user_id]['selected_categories']

            if not selected:
                update.message.reply_text("⚠️ الرجاء اختيار تصنيف واحد على الأقل!")
                return

            category_names = [CATEGORIES[cat] for cat in selected]

            success_message = f"""✅ تم تسجيلك بنجاح!

ستتابع التصنيفات التالية:
{chr(10).join(['• ' + name for name in category_names])}

سأرسل لك المشاريع الجديدة فور نزولها 🔔

الأوامر:
/categories - تغيير التصنيفات
/stop - إيقاف"""

            update.message.reply_text(success_message, reply_markup=ReplyKeyboardRemove())
            logger.info(f"✅ تسجيل المستخدم {user_id} مع {len(selected)} تصنيفات")
            return

        # معالج الاختيار
        try:
            category_num = text.split('.')[0].strip()

            if category_num not in CATEGORIES:
                update.message.reply_text("❌ اختيار غير صحيح!")
                return

            selected = user_data_store[user_id]['selected_categories']

            if category_num in selected:
                selected.remove(category_num)
                status = "❌ تم الحذف"
            else:
                selected.append(category_num)
                status = "✅ تم الإضافة"

            update.message.reply_text(
                f"{status}: {CATEGORIES[category_num]}\n\n"
                f"المختار: ({len(selected)})\n" +
                '\n'.join([f"• {CATEGORIES[c]}" for c in selected])
            )

        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            update.message.reply_text("❌ حدث خطأ!")

    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")


def stop_command(bot, update):
    """معالج أمر /stop"""
    try:
        user_id = update.message.from_user.id
        if user_id in user_data_store:
            del user_data_store[user_id]
        update.message.reply_text("👋 تم الإيقاف!", reply_markup=ReplyKeyboardRemove())
        logger.info(f"👋 المستخدم {user_id} توقف عن البوت")
    except Exception as e:
        logger.error(f"❌ خطأ في /stop: {e}")


def categories_command(bot, update):
    """معالج أمر /categories"""
    try:
        keyboard = []
        for key, value in CATEGORIES.items():
            keyboard.append([f"{key}. {value}"])
        keyboard.append(["✅ تأكيد"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text("اختر التصنيفات:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"❌ خطأ في /categories: {e}")


def main():
    """بدء البوت"""
    if not TELEGRAM_TOKEN:
        print("❌ خطأ: TELEGRAM_TOKEN غير محدد!")
        return

    # إنشاء البوت
    request = Request(connect_timeout=15, read_timeout=15)
    bot = Bot(token=TELEGRAM_TOKEN, request=request)

    # اختبار الاتصال
    try:
        info = bot.get_me()
        logger.info(f"✅ اتصال البوت نجح: @{info.username}")
    except Exception as e:
        logger.error(f"❌ خطأ في الاتصال: {e}")
        print(f"❌ خطأ في الاتصال: {e}")
        return

    # إنشاء dispatcher
    from telegram.ext import Dispatcher
    dispatcher = Dispatcher(bot, None, workers=1)

    # إضافة معالجات
    from telegram.ext import CommandHandler, MessageHandler, Filters

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('stop', stop_command))
    dispatcher.add_handler(CommandHandler('categories', categories_command))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    # بدء البوت
    print("\n" + "="*60)
    print("✅ البوت يعمل الآن!")
    print("="*60)
    print(f"🤖 البوت: @Freelancer_Here_bot")
    print(f"👤 المسؤول: @Elzero7 (ID: {ADMIN_ID})")
    print(f"📢 القناة: Freelancer (ID: {FREELANCER_CHANNEL_ID})")
    print("="*60)
    print("\n⏳ في انتظار الرسائل...")
    print("\n💡 اختبر البوت على Telegram:\n   /start\n")
    print("="*60 + "\n")

    logger.info("🚀 بدء البوت!")

    try:
        bot.set_webhook()
        dispatcher.start_polling(poll_interval=1)
    except KeyboardInterrupt:
        print("\n\n👋 توقف البوت")
        logger.info("👋 توقف البوت")
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        print(f"❌ خطأ: {e}")


if __name__ == '__main__':
    main()


