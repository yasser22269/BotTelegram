#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
بوت مستقل - نسخة مبسطة
Mustaqbal Bot - Simplified Version
"""

import logging
import os
import json
from dotenv import load_dotenv
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
import threading
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

# حالات المحادثة
SELECTING_CATEGORIES = 1

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

# تخزين البيانات مؤقتاً
user_data_store = {}


def start(bot, update):
    """معالج أمر /start"""
    user = update.message.from_user
    user_id = user.id

    welcome_message = f"""
مرحباً {user.first_name} 👋

أنا بوت مستقل - أساعدك في متابعة المشاريع الجديدة على منصة مستقل 🚀

اختر التصنيفات التي تهمك:
    """

    # إنشاء لوحة المفاتيح
    keyboard = []
    for key, value in CATEGORIES.items():
        keyboard.append([f"{key}. {value}"])
    keyboard.append(["✅ تأكيد الاختيار"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(welcome_message, reply_markup=reply_markup)

    # تهيئة البيانات
    user_data_store[user_id] = {'selected_categories': []}

    return SELECTING_CATEGORIES


def handle_category_selection(bot, update):
    """معالج اختيار التصنيفات"""
    user = update.message.from_user
    user_id = user.id
    text = update.message.text

    if user_id not in user_data_store:
        user_data_store[user_id] = {'selected_categories': []}

    # التحقق من أمر التأكيد
    if text == "✅ تأكيد الاختيار":
        selected = user_data_store[user_id]['selected_categories']

        if not selected:
            update.message.reply_text("⚠️ الرجاء اختيار تصنيف واحد على الأقل!")
            return SELECTING_CATEGORIES

        category_names = [CATEGORIES[cat] for cat in selected]

        success_message = f"""
✅ تم تسجيلك بنجاح!

ستتابع التصنيفات التالية:
{chr(10).join(['• ' + name for name in category_names])}

سأرسل لك المشاريع الجديدة فور نزولها 🔔

الأوامر المتاحة:
/categories - تغيير التصنيفات
/stop - إيقاف المتابعة
        """

        update.message.reply_text(success_message, reply_markup=ReplyKeyboardRemove())

        # حفظ البيانات
        logger.info(f"✅ تم تسجيل المستخدم {user_id} مع التصنيفات: {selected}")

        return ConversationHandler.END

    # استخراج رقم التصنيف
    try:
        category_num = text.split('.')[0].strip()

        if category_num not in CATEGORIES:
            update.message.reply_text("❌ اختيار غير صحيح. حاول مجدداً!")
            return SELECTING_CATEGORIES

        # إضافة التصنيف
        selected = user_data_store[user_id]['selected_categories']

        if category_num in selected:
            selected.remove(category_num)
            update.message.reply_text(f"❌ تم إزالة: {CATEGORIES[category_num]}")
        else:
            selected.append(category_num)
            update.message.reply_text(f"✅ تم إضافة: {CATEGORIES[category_num]}")

        message = f"التصنيفات المختارة ({len(selected)}):\n\n"
        for cat_id in selected:
            message += f"• {CATEGORIES[cat_id]}\n"

        update.message.reply_text(message)

    except Exception as e:
        logger.error(f"خطأ في معالجة الاختيار: {e}")
        update.message.reply_text("❌ حدث خطأ. حاول مجدداً!")

    return SELECTING_CATEGORIES


def categories_command(bot, update):
    """معالج أمر تغيير التصنيفات"""
    keyboard = []
    for key, value in CATEGORIES.items():
        keyboard.append([f"{key}. {value}"])
    keyboard.append(["✅ تأكيد الاختيار"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "اختر التصنيفات الجديدة:",
        reply_markup=reply_markup
    )

    return SELECTING_CATEGORIES


def stop_command(bot, update):
    """معالج أمر التوقف"""
    user_id = update.message.from_user.id

    if user_id in user_data_store:
        del user_data_store[user_id]

    update.message.reply_text(
        "👋 تم إيقاف المتابعة. يمكنك استخدام /start للعودة في أي وقت.",
        reply_markup=ReplyKeyboardRemove()
    )


def error(bot, update, error):
    """معالج الأخطاء"""
    logger.warning(f'تم تحديث {update} خطأ {error}')


def main():
    """بدء البوت"""
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN غير محدد في ملف .env")

    # إنشاء updater
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    # معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_CATEGORIES: [
                MessageHandler(Filters.text, handle_category_selection)
            ],
        },
        fallbacks=[
            CommandHandler("stop", stop_command),
            CommandHandler("categories", categories_command)
        ],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("stop", stop_command))
    dp.add_handler(CommandHandler("categories", categories_command))

    # معالج الأخطاء
    dp.add_error_handler(error)

    # بدء البوت
    logger.info("🚀 جاري بدء البوت...")
    print("\n" + "="*60)
    print("✅ البوت يعمل الآن!")
    print("="*60)
    print(f"👤 معرف الإدمن: {ADMIN_ID}")
    print(f"📢 معرف القناة: {FREELANCER_CHANNEL_ID}")
    print(f"🤖 البوت: @Freelancer_Here_bot")
    print("="*60)
    print("\n اختبر البوت على Telegram الآن!")
    print("="*60 + "\n")

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

