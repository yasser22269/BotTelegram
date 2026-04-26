"""
بوت تيليجرام لمراقبة مشاريع مستقل
"""
import logging
import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from database import Database
from advanced_scraper import MustaqbalScraper
from config import TELEGRAM_TOKEN, ADMIN_ID, SCRAPE_INTERVAL, CATEGORIES, MESSAGES, FREELANCER_CHANNEL_ID, SEND_TO_CHANNEL

# تحميل متغيرات البيئة
load_dotenv()

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
SELECTING_CATEGORIES = 1

# قاعدة البيانات
db = Database()

# الـ Scraper
scraper = MustaqbalScraper()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالج أمر /start"""
    user = update.effective_user

    welcome_message = MESSAGES['welcome'].format(first_name=user.first_name)


    # إنشاء لوحة المفاتيح بالتصنيفات
    keyboard = []
    for key, value in CATEGORIES.items():
        keyboard.append([f"{key}. {value}"])

    keyboard.append(["✅ تأكيد الاختيار"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    return SELECTING_CATEGORIES


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالج اختيار التصنيفات"""
    user = update.effective_user
    text = update.message.text

    # التحقق من أمر التأكيد
    if text == "✅ تأكيد الاختيار":
        selected = context.user_data.get('selected_categories', [])

        if not selected:
            await update.message.reply_text("⚠️ الرجاء اختيار تصنيف واحد على الأقل!")
            return SELECTING_CATEGORIES

        # حفظ المستخدم في قاعدة البيانات
        db.add_user(user.id, user.username, selected)

        category_names = [CATEGORIES[cat] for cat in selected]
        categories_text = '\n'.join(['• ' + name for name in category_names])

        success_message = MESSAGES['confirm_categories'].format(categories=categories_text)


        await update.message.reply_text(success_message, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # استخراج رقم التصنيف
    try:
        category_num = text.split('.')[0].strip()

        if category_num not in CATEGORIES:
            await update.message.reply_text("❌ اختيار غير صحيح. حاول مجدداً!")
            return SELECTING_CATEGORIES

        # إضافة التصنيف للقائمة المختارة
        if 'selected_categories' not in context.user_data:
            context.user_data['selected_categories'] = []

        if category_num in context.user_data['selected_categories']:
            context.user_data['selected_categories'].remove(category_num)
            await update.message.reply_text(f"❌ تم إزالة: {CATEGORIES[category_num]}")
        else:
            context.user_data['selected_categories'].append(category_num)
            await update.message.reply_text(f"✅ تم إضافة: {CATEGORIES[category_num]}")

        selected = context.user_data['selected_categories']
        message = f"التصنيفات المختارة ({len(selected)}):\n\n"
        for cat_id in selected:
            message += f"• {CATEGORIES[cat_id]}\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"خطأ في معالجة الاختيار: {e}")
        await update.message.reply_text("❌ حدث خطأ. حاول مجدداً!")

    return SELECTING_CATEGORIES


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالج أمر تغيير التصنيفات"""
    keyboard = []
    for key, value in CATEGORIES.items():
        keyboard.append([f"{key}. {value}"])
    keyboard.append(["✅ تأكيد الاختيار"])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "اختر التصنيفات الجديدة:",
        reply_markup=reply_markup
    )

    return SELECTING_CATEGORIES


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر التوقف"""
    user_id = update.effective_user.id

    db.deactivate_user(user_id)

    await update.message.reply_text(
        "👋 تم إيقاف المتابعة. يمكنك استخدام /start للعودة في أي وقت.",
        reply_markup=ReplyKeyboardRemove()
    )


async def scrape_new_projects(context: ContextTypes.DEFAULT_TYPE) -> None:
    """مهمة دورية لفحص المشاريع الجديدة"""
    logger.info("🔍 جاري البحث عن مشاريع جديدة...")

    try:
        # الحصول على جميع المستخدمين النشطين
        active_users = db.get_all_active_users()
        sent_projects_in_this_cycle = set()

        for user_id, categories in active_users:
            for category_id in categories:
                try:
                    # جلب المشاريع الجديدة باستخدام Scraper
                    new_projects = scraper.get_new_projects(category_id)

                    if new_projects:
                        logger.info(f"✅ وجدت {len(new_projects)} مشروع جديد في التصنيف {CATEGORIES[category_id]}")

                        for project in new_projects:
                            try:
                                # تجنب إرسال المشروع مرتين
                                if project.get('id') in sent_projects_in_this_cycle:
                                    continue

                                message = MESSAGES['new_project'].format(
                                    title=project.get('title', 'بدون عنوان'),
                                    description=project.get('description', '')[:150],
                                    budget=project.get('budget', 'غير محدد'),
                                    level=project.get('level', 'غير محدد'),
                                    date=project.get('posted_date', ''),
                                    url=project.get('url', '')
                                )

                                # إرسال للمستخدم الفردي
                                await context.bot.send_message(
                                    chat_id=user_id,
                                    text=message,
                                    parse_mode='HTML'
                                )

                                # إرسال للقناة إذا كانت مفعّلة
                                if SEND_TO_CHANNEL:
                                    try:
                                        channel_message = f"📢 <b>منصة مستقل</b>\n\n{message}\n\n#مستقل #{CATEGORIES[category_id].replace(' ', '_')}"
                                        await context.bot.send_message(
                                            chat_id=FREELANCER_CHANNEL_ID,
                                            text=channel_message,
                                            parse_mode='HTML'
                                        )
                                        logger.info(f"📢 تم إرسال المشروع للقناة")
                                    except Exception as e:
                                        logger.warning(f"⚠️ خطأ في إرسال المشروع للقناة: {e}")

                                # حفظ المشروع المرسل
                                db.save_sent_project(
                                    project.get('id'),
                                    project.get('title'),
                                    project.get('description'),
                                    CATEGORIES.get(category_id),
                                    project.get('url'),
                                    user_id
                                )

                                sent_projects_in_this_cycle.add(project.get('id'))

                                # تأخير صغير بين الرسائل
                                await asyncio.sleep(0.5)

                            except Exception as e:
                                logger.error(f"خطأ في إرسال المشروع: {e}")

                except Exception as e:
                    logger.error(f"خطأ في فحص التصنيف {category_id}: {e}")

    except Exception as e:
        logger.error(f"خطأ في مهمة scraping: {e}")



async def post_init(application: Application) -> None:
    """إعداد المهام الدورية بعد بدء التطبيق"""
    scheduler = AsyncIOScheduler()

    # إضافة مهمة فحص المشاريع الجديدة
    scheduler.add_job(
        scrape_new_projects,
        trigger=IntervalTrigger(seconds=SCRAPE_INTERVAL),
        args=(application.context_types.context,),
        id='scrape_projects',
        name='فحص المشاريع الجديدة',
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ تم بدء المهام الدورية")


def main() -> None:
    """بدء البوت"""
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN غير محدد في ملف .env")

    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_CATEGORIES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)
            ],
        },
        fallbacks=[
            CommandHandler("stop", stop_command),
            CommandHandler("categories", categories_command)
        ],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("categories", categories_command))

    # بدء البوت
    logger.info("🚀 جاري بدء البوت...")
    application.run_polling()


if __name__ == '__main__':
    main()

