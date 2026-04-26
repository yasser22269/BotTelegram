#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Freelancer Bot - channel-native subscriptions, mostaql scraper
"""

import sys
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import re
import json
import logging
import time
import threading
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from telegram import (Bot, InlineKeyboardMarkup, InlineKeyboardButton,
                       ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.utils.request import Request

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN        = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID              = int(os.getenv('ADMIN_ID', '0'))
FREELANCER_CHANNEL_ID = int(os.getenv('FREELANCER_CHANNEL_ID', '0'))
SCRAPE_INTERVAL       = int(os.getenv('SCRAPE_INTERVAL', '300'))

DATA_FILE = os.path.join(os.path.dirname(__file__), 'users_data.json')

ALL_CATEGORIES = {
    "1": "أعمال وخدمات استشارية",
    "2": "برمجة، تطوير المواقع والتطبيقات",
    "3": "ذكاء اصطناعي وتعلم الآلة",
    "4": "هندسة، عمارة وتصميم داخلي",
    "5": "تصميم، فيديو وصوتيات",
    "6": "تسويق إلكتروني ومبيعات",
    "7": "كتابة، تحرير، ترجمة ولغات",
    "8": "دعم، مساعدة وإدخال بيانات",
    "9": "تدريب وتعليم عن بعد",
}

CAT_KEYWORDS = {
    "2": ["برمجة", "تطوير", "موقع", "تطبيق", "ويب", "web", "app"],
    "3": ["ذكاء اصطناعي", "تعلم الآلة", "ai", "machine learning", "gpt"],
    "4": ["هندسة", "عمارة", "تصميم داخلي", "معماري"],
    "5": ["تصميم", "فيديو", "صوتيات", "مونتاج", "جرافيك"],
    "6": ["تسويق", "مبيعات", "إعلانات", "سوشيال", "seo"],
    "7": ["كتابة", "ترجمة", "تحرير", "محتوى", "مقالات"],
    "8": ["دعم", "إدخال بيانات", "سكرتارية", "خدمة عملاء"],
    "9": ["تدريب", "تعليم", "دورات", "شرح"],
    "1": ["أعمال", "استشارات", "استشار", "إدارة"],
}

ACTIVE_CATEGORIES = {"2"}   # Only these categories are scraped and notified

# ── Upwork OAuth 2.0 credentials (from .env) ──────────────────────────────────
UPWORK_CLIENT_ID      = os.getenv('UPWORK_CLIENT_ID', '')
UPWORK_CLIENT_SECRET  = os.getenv('UPWORK_CLIENT_SECRET', '')
_upwork_access_token  = os.getenv('UPWORK_ACCESS_TOKEN', '')
_upwork_refresh_token = os.getenv('UPWORK_REFRESH_TOKEN', '')

users            = {}   # {user_id(int): {"name", "chat_id", "categories"}}
seen_ids         = set()
upwork_seen_ids  = set()
admin_state      = {}
last_id          = 0
BOT_USERNAME     = ""   # set after get_me()


# ── Storage ───────────────────────────────────────────────────────────────────

def load_data():
    global users, seen_ids, upwork_seen_ids
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        users           = {int(k): v for k, v in data.get('users', {}).items()}
        seen_ids        = set(data.get('seen_ids', []))
        upwork_seen_ids = set(data.get('upwork_seen_ids', []))
    logger.info(f"تم تحميل {len(users)} مستخدم، {len(seen_ids)} مستقل / {len(upwork_seen_ids)} Upwork")


def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'users':           {str(k): v for k, v in users.items()},
            'seen_ids':        list(seen_ids)[-2000:],
            'upwork_seen_ids': list(upwork_seen_ids)[-2000:],
        }, f, ensure_ascii=False, indent=2)


# ── Keyboards ─────────────────────────────────────────────────────────────────

def reply_category_keyboard(selected):
    rows = []
    for k, v in ALL_CATEGORIES.items():
        prefix = "✅ " if k in selected else ""
        rows.append([f"{prefix}{k}. {v}"])
    rows.append(["✔️ تأكيد التصنيفات"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def channel_menu_keyboard():
    """Inline keyboard for the subscription menu posted in channel."""
    rows = []
    for k, v in ALL_CATEGORIES.items():
        rows.append([InlineKeyboardButton(f"🔔 {v}", callback_data=f"sub_{k}")])
    rows.append([InlineKeyboardButton("📋 اشتراكاتي الحالية", callback_data="my_subs")])
    return InlineKeyboardMarkup(rows)


def job_subscribe_keyboard(cat_id):
    """Subscribe button on job posts — uses jsub_ prefix (subscribe-only, no toggle)."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"🔔 اشترك في {ALL_CATEGORIES.get(cat_id, 'هذا التصنيف')}",
            callback_data=f"jsub_{cat_id}"
        ),
        InlineKeyboardButton("📋 اشتراكاتي", callback_data="my_subs"),
    ]])


# ── Callback query (channel button clicks) ───────────────────────────────────

def handle_callback(bot, cq):
    user_id = cq.from_user.id
    name    = cq.from_user.first_name or 'صديقي'
    data    = cq.data or ''

    # Ensure user record exists
    if user_id not in users:
        users[user_id] = {"name": name, "chat_id": user_id, "categories": []}
    users[user_id]["name"] = name

    if data.startswith("jsub_"):
        # Subscribe-only from job posts — never unsubscribe
        cat = data[5:]
        if cat not in ALL_CATEGORIES:
            bot.answer_callback_query(cq.id, "❌ تصنيف غير صحيح")
            return

        cats = users[user_id].setdefault("categories", [])
        if cat in cats:
            bot.answer_callback_query(
                cq.id,
                f"✅ أنت مشترك بالفعل في:\n{ALL_CATEGORIES[cat]}\n\nستصلك المشاريع الجديدة تلقائياً",
                show_alert=True
            )
            return

        cats.append(cat)
        save_data()
        confirm = f"✅ تم الاشتراك في:\n{ALL_CATEGORIES[cat]}\n\nستصلك المشاريع الجديدة فور نزولها 🔔"
        try:
            bot.send_message(user_id, confirm)
            bot.answer_callback_query(cq.id, "✅ تم الاشتراك!", show_alert=False)
        except Exception:
            bot.answer_callback_query(cq.id, confirm, show_alert=True)

    elif data.startswith("sub_"):
        # Toggle from the subscription menu
        cat = data[4:]
        if cat not in ALL_CATEGORIES:
            bot.answer_callback_query(cq.id, "❌ تصنيف غير صحيح")
            return

        cats = users[user_id].setdefault("categories", [])
        if cat in cats:
            cats.remove(cat)
            msg = f"❌ تم إلغاء الاشتراك في:\n{ALL_CATEGORIES[cat]}"
        else:
            cats.append(cat)
            msg = f"✅ تم الاشتراك في:\n{ALL_CATEGORIES[cat]}"

        save_data()
        try:
            bot.send_message(user_id, msg)
            bot.answer_callback_query(cq.id, msg, show_alert=False)
        except Exception:
            bot.answer_callback_query(cq.id, msg, show_alert=True)

    elif data == "my_subs":
        cats = users[user_id].get("categories", [])
        if cats:
            txt = "📋 اشتراكاتك الحالية:\n\n" + "\n".join(
                [f"• {ALL_CATEGORIES[c]}" for c in cats])
        else:
            txt = "لم تشترك في أي تصنيف بعد.\nانقر على التصنيفات للاشتراك."
        bot.answer_callback_query(cq.id, "✅ تم الإرسال لرسائلك الخاصة", show_alert=False)
        try:
            bot.send_message(user_id, txt)
        except Exception:
            bot.answer_callback_query(
                cq.id,
                f"افتح البوت أولاً:\n@{BOT_USERNAME}",
                show_alert=True,
            )


# ── User handlers ─────────────────────────────────────────────────────────────

def handle_start(bot, chat_id, user_id, name):
    # Update chat_id (critical for DMs after channel subscription)
    if user_id not in users:
        users[user_id] = {"name": name, "chat_id": chat_id, "categories": []}
    else:
        users[user_id].update({"chat_id": chat_id, "name": name})
    save_data()

    cats = users[user_id]["categories"]
    if cats:
        # Already has subscriptions from channel buttons
        cat_names = "\n".join([f"• {ALL_CATEGORIES[c]}" for c in cats])
        bot.send_message(
            chat_id,
            f"مرحباً {name} 👋\n\n"
            f"✅ اشتراكاتك الحالية:\n{cat_names}\n\n"
            f"يمكنك تغييرها من قائمة التصنيفات في القناة\n"
            f"أو استخدم /edit لتعديلها هنا.",
        )
    else:
        bot.send_message(
            chat_id,
            f"مرحباً {name} 👋\n\n"
            f"اشترك في التصنيفات مباشرة من القناة 📢\n"
            f"أو اختر من هنا:",
            reply_markup=reply_category_keyboard([])
        )


def handle_edit(bot, chat_id, user_id, name):
    cats = users.get(user_id, {}).get("categories", [])
    bot.send_message(
        chat_id,
        "اختر التصنيفات:",
        reply_markup=reply_category_keyboard(cats)
    )


def handle_confirm(bot, chat_id, user_id):
    cats = users[user_id]["categories"]
    if not cats:
        bot.send_message(chat_id, "⚠️ لم تختر أي تصنيف!")
        return
    lines = ["✅ تم الاشتراك في:\n"] + [f"• {ALL_CATEGORIES[c]}" for c in cats]
    lines.append("\n/stop للإيقاف  |  /edit لتعديل التصنيفات")
    bot.send_message(chat_id, "\n".join(lines), reply_markup=ReplyKeyboardRemove())
    save_data()


def handle_stop(bot, chat_id, user_id):
    users.pop(user_id, None)
    save_data()
    bot.send_message(chat_id, "👋 تم إلغاء اشتراكك بنجاح.", reply_markup=ReplyKeyboardRemove())


def handle_mystats(bot, chat_id, user_id):
    cats = users.get(user_id, {}).get("categories", [])
    lines = (["📋 تصنيفاتك:\n"] + [f"• {ALL_CATEGORIES[c]}" for c in cats]
             if cats else ["لم تشترك في أي تصنيف بعد."])
    bot.send_message(chat_id, "\n".join(lines))


def toggle_category(bot, chat_id, user_id, cat):
    cats = users[user_id].setdefault("categories", [])
    if cat in cats:
        cats.remove(cat)
        status = f"❌ تم إلغاء: {ALL_CATEGORIES[cat]}"
    else:
        cats.append(cat)
        status = f"✅ تمت الإضافة: {ALL_CATEGORIES[cat]}"
    bot.send_message(chat_id, status, reply_markup=reply_category_keyboard(cats))


# ── Broadcast helper ──────────────────────────────────────────────────────────

def broadcast(bot, content, target_cats, keyboard=None, reporter_chat_id=None):
    channel_ok = False
    try:
        bot.send_message(FREELANCER_CHANNEL_ID, content,
                         reply_markup=keyboard, parse_mode=None)
        channel_ok = True
    except Exception as e:
        logger.error(f"القناة: {e}")

    targets = [u for u in users.values()
               if any(c in u.get("categories", []) for c in target_cats)]
    sent = failed = 0
    for u in targets:
        try:
            bot.send_message(u["chat_id"], content)
            sent += 1
            time.sleep(0.05)
        except Exception:
            failed += 1

    if reporter_chat_id:
        cat_names = "\n".join([f"• {ALL_CATEGORIES[c]}" for c in target_cats])
        channel_status = "✅ نُشر في القناة" if channel_ok else "❌ فشل النشر في القناة"
        bot.send_message(
            reporter_chat_id,
            f"✅ تم الإرسال!\n\n"
            f"📢 القناة: {channel_status}\n"
            f"📂 التصنيفات:\n{cat_names}\n\n"
            f"👥 المستهدفون: {len(targets)}\n"
            f"✅ نجح: {sent}  |  ❌ فشل: {failed}"
        )
    return sent, failed


# ── Admin: /menu ──────────────────────────────────────────────────────────────

def post_channel_menu(bot, chat_id):
    """Post subscription menu with inline buttons to the channel."""
    try:
        bot.send_message(
            FREELANCER_CHANNEL_ID,
            "🔔 اشترك في التصنيفات التي تريد متابعتها\n\n"
            "انقر على التصنيف لتفعيل أو إلغاء الاشتراك:",
            reply_markup=channel_menu_keyboard()
        )
        bot.send_message(chat_id, "✅ تم نشر قائمة الاشتراك في القناة.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل: {e}")


# ── Admin: /post ──────────────────────────────────────────────────────────────

def admin_post_step1(bot, chat_id, admin_id, text):
    header = text.replace("/post", "").strip()
    target_cats = (list(ALL_CATEGORIES.keys()) if header.lower() == "all"
                   else [c.strip() for c in header.split(",") if c.strip() in ALL_CATEGORIES])
    if not target_cats:
        bot.send_message(chat_id, "❌ مثال:\n/post 1,2,3\nأو:\n/post all")
        return
    admin_state[admin_id] = {"step": "waiting_content", "categories": target_cats}
    cat_names = "\n".join([f"• {ALL_CATEGORIES[c]}" for c in target_cats])
    bot.send_message(chat_id,
        f"📂 التصنيفات المستهدفة:\n{cat_names}\n\nأرسل المحتوى (أو /cancel):")


def admin_post_step2(bot, chat_id, admin_id, content):
    state = admin_state.pop(admin_id, None)
    if not state:
        return
    cats = state["categories"]
    # Attach subscribe button if single category
    kb = job_subscribe_keyboard(cats[0]) if len(cats) == 1 else None
    broadcast(bot, content, cats, keyboard=kb, reporter_chat_id=chat_id)


# ── Admin: /newpost wizard ────────────────────────────────────────────────────

NEWPOST_STEPS = [
    ("np_title",    "🎯 عنوان المشروع؟"),
    ("np_site",     "🌐 اسم الموقع المصدر؟\nمثال: mostaql.com"),
    ("np_client",   "👤 اسم العميل؟"),
    ("np_role",     "💼 مسمى العميل الوظيفي؟"),
    ("np_budget",   "💵 الميزانية؟\nمثال: $500 - $1000"),
    ("np_duration", "⌛ المدة؟\nمثال: 30 يوماً"),
    ("np_rating",   "📊 تقييم العميل؟  أو  - للتخطي"),
    ("np_desc",     "✍️ الوصف الكامل؟"),
    ("np_link",     "🔗 رابط المشروع؟"),
    ("np_cats",     "📂 التصنيفات؟\nمثال: 1,2,3  أو  all"),
]


def newpost_start(bot, chat_id, admin_id):
    admin_state[admin_id] = {"step": "np_site", "data": {}}
    bot.send_message(chat_id, "📝 بوست جديد — /cancel للإلغاء\n\n" + NEWPOST_STEPS[0][1])


def newpost_next(bot, chat_id, admin_id, answer):
    state = admin_state.get(admin_id)
    if not state:
        return
    state["data"][state["step"]] = answer.strip()
    step_keys = [s[0] for s in NEWPOST_STEPS]
    idx = step_keys.index(state["step"])
    if idx + 1 < len(NEWPOST_STEPS):
        nxt = NEWPOST_STEPS[idx + 1]
        state["step"] = nxt[0]
        bot.send_message(chat_id, nxt[1])
    else:
        state["step"] = "np_confirm"
        bot.send_message(chat_id,
            f"👁 معاينة:\n\n{build_post(state['data'])}\n\nإرسل ✅ للتأكيد أو /cancel")


def build_post(d):
    rating  = d.get("np_rating", "").strip()
    link    = d.get("np_link",   "").strip()
    rating_line = f"📊 {rating}\n" if rating and rating != "-" else ""
    link_line   = f"\n🔗 {link}"  if link  and link  != "-" else ""
    return (
        f"🌐 المصدر: {d.get('np_site','')}\n\n"
        f"🎯 {d.get('np_title','')}\n"
        f"👤 {d.get('np_client','')}\n"
        f"💼 {d.get('np_role','')}\n"
        f"💵 {d.get('np_budget','')}\n"
        f"⌛ {d.get('np_duration','')}\n"
        f"{rating_line}"
        f"\n~~~~ الوصف ~~~~\n"
        f"{d.get('np_desc','')}"
        f"{link_line}"
    )


def newpost_confirm(bot, chat_id, admin_id):
    state = admin_state.pop(admin_id, None)
    if not state:
        return
    cats_raw = state["data"].get("np_cats", "").strip()
    target_cats = (list(ALL_CATEGORIES.keys()) if cats_raw.lower() == "all"
                   else [c.strip() for c in cats_raw.split(",") if c.strip() in ALL_CATEGORIES])
    if not target_cats:
        bot.send_message(chat_id, "❌ تصنيفات غير صحيحة، تم الإلغاء.")
        return
    kb = job_subscribe_keyboard(target_cats[0]) if len(target_cats) == 1 else None
    broadcast(bot, build_post(state["data"]), target_cats, keyboard=kb,
              reporter_chat_id=chat_id)


# ── Admin: /stats, /users ─────────────────────────────────────────────────────

def admin_stats(bot, chat_id):
    lines = [f"📊 إحصائيات\n", f"👥 المشتركون: {len(users)}\n"]
    for k, v in ALL_CATEGORIES.items():
        count = sum(1 for u in users.values() if k in u.get("categories", []))
        lines.append(f"{k}. {v}: {count}")
    bot.send_message(chat_id, "\n".join(lines))


def admin_users(bot, chat_id):
    if not users:
        bot.send_message(chat_id, "لا يوجد مشتركون."); return
    lines = [f"👥 المشتركون ({len(users)}):\n"]
    for uid, u in list(users.items())[:50]:
        cats = ", ".join(u.get("categories", [])) or "—"
        lines.append(f"• {u['name']} [{uid}] ← {cats}")
    bot.send_message(chat_id, "\n".join(lines))


def admin_test(bot, chat_id):
    """Send a real project from mostaql as a test notification to the admin only."""
    bot.send_message(chat_id, "⏳ جاري جلب مشروع تجريبي من مستقل...")
    try:
        projects = fetch_listing()
        if not projects:
            bot.send_message(chat_id, "❌ لم أجد مشاريع في مستقل الآن.")
            return
        pid, url = next(iter(projects.items()))
        p = scrape_project(url)
        cat_id   = p.get('category_id')
        cat_name = ALL_CATEGORIES.get(cat_id, 'غير معروف') if cat_id else 'غير معروف'
        content  = format_scraped(p)
        bot.send_message(
            chat_id,
            f"🧪 مشروع تجريبي — التصنيف المكتشف: [{cat_name}]\n\n{content}"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {e}")


# ── New-member handler ────────────────────────────────────────────────────────

def handle_new_member(bot, cm):
    """Called when someone joins the channel — show category selection."""
    if cm.chat.id != FREELANCER_CHANNEL_ID:
        return
    member = cm.new_chat_member
    if not member or member.status not in ('member', 'administrator'):
        return
    user = member.user
    if not user or user.is_bot:
        return

    user_id = user.id
    name    = user.first_name or 'صديقي'

    if user_id not in users:
        users[user_id] = {"name": name, "chat_id": user_id, "categories": []}
    users[user_id]["name"] = name
    save_data()

    welcome = (
        f"أهلاً {name} 👋\n\n"
        "📌 كيف تشتغل المنصة:\n"
        "1️⃣ اضغط على التصنيف الذي يهمك من الأزرار أدناه\n"
        "2️⃣ يمكنك الاشتراك في أكثر من تصنيف\n"
        "3️⃣ كل ما ينزل مشروع جديد في تصنيفاتك ستصلك رسالة فوراً\n\n"
        "⬇️ اختر تصنيفاتك الآن:"
    )

    # Try DM first; if user hasn't started bot, post buttons directly in channel
    try:
        bot.send_message(user_id, welcome, reply_markup=channel_menu_keyboard())
    except Exception:
        try:
            bot.send_message(
                FREELANCER_CHANNEL_ID,
                welcome,
                reply_markup=channel_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"handle_new_member fallback: {e}")


# ── Scraper ───────────────────────────────────────────────────────────────────

SCRAPE_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/120.0.0.0 Safari/537.36'),
    'Accept-Language': 'ar,en-US;q=0.9',
}


def map_category(text):
    """Keyword fallback — used only when breadcrumb extraction fails."""
    text = text or ''
    for cat_id, cat_name in ALL_CATEGORIES.items():
        if cat_name in text:
            return cat_id
    for cat_id, keywords in CAT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat_id
    return None


def extract_category_from_breadcrumb(soup):
    """Primary method: read the category directly from the mostaql breadcrumb."""
    for a in soup.select('.breadcrumb a'):
        name = a.get_text(strip=True)
        for cat_id, cat_name in ALL_CATEGORIES.items():
            if cat_name == name:
                return cat_id
    return None


def fetch_listing():
    resp = requests.get('https://mostaql.com/projects',
                        headers=SCRAPE_HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    result = {}
    for a in soup.select('h2 a, h3 a'):
        href = a.get('href', '')
        if '/project/' not in href:
            continue
        m = re.search(r'/project/(\d+)-', href)
        if m:
            pid = int(m.group(1))
            url = href if href.startswith('http') else 'https://mostaql.com' + href
            result[pid] = url
    return result


def scrape_project(url):
    resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)

    title = ''
    if soup.title:
        title = re.sub(r'\s*[|\-–]\s*مستقل.*$', '',
                       soup.title.string or '', flags=re.I).strip()
    if not title:
        h = soup.find('h1') or soup.find('h2')
        title = h.get_text(strip=True) if h else ''

    bm = re.search(r'\$[\d,]+\.?\d*\s*[-–]\s*\$[\d,]+\.?\d*', text)
    budget = bm.group(0).strip() if bm else ''

    dm = re.search(r'(\d+)\s*(يوماً|يوما|يوم|أيام)', text)
    duration = f"{dm.group(1)} {dm.group(2)}" if dm else ''

    rm = re.search(r'(\d+\.\d+)\s*%', text)
    rating = f"{rm.group(1)}%" if rm else ''

    date_m = re.search(
        r'(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})',
        text)
    date_str = (f"{date_m.group(1)} {date_m.group(2)} {date_m.group(3)}"
                if date_m else datetime.now().strftime('%d/%m/%Y'))

    client = ''
    client_a = soup.find('a', href=re.compile(r'mostaql\.com/users/|^/users/'))
    if client_a:
        client = client_a.get_text(strip=True)

    # Extract category: breadcrumb first, keyword fallback second
    category_id = extract_category_from_breadcrumb(soup) or map_category(text)

    # Extract actual project description from mostaql's content card
    desc = ''
    content_el = soup.select_one('.carda__content')
    if content_el:
        desc = content_el.get_text(separator='\n', strip=True)
    if not desc:
        # Fallback: look for a sufficiently long paragraph that isn't navigation
        for tag in soup.find_all('p'):
            t = tag.get_text(strip=True)
            if 50 < len(t) < 2000 and len(t) > len(desc):
                desc = t

    return {
        'title':       title,
        'client':      client,
        'budget':      budget,
        'duration':    duration,
        'rating':      rating,
        'date':        date_str,
        'category_id': category_id,
        'description': desc[:700],
        'url':         url,
    }


def format_scraped(p):
    client_line   = f"👤 {p['client']}\n"                                          if p.get('client')      else ""
    budget_line   = f"💵 {p['budget']}\n"                                          if p.get('budget')      else ""
    dur_line      = f"⌛ {p['duration']}\n"                                        if p.get('duration')    else ""
    rating_line   = f"📊 {p['rating']}\n"                                          if p.get('rating')      else ""
    date_line     = f"✍️ {p['date']}\n"                                            if p.get('date')        else ""
    cat_id        = p.get('category_id')
    cat_line      = f"📂 {ALL_CATEGORIES[cat_id]}\n"                               if cat_id               else ""
    return (
        f"🎯 {p['title']}\n"
        f"🌐 المصدر: mostaql.com\n\n"
        f"{cat_line}"
        f"{client_line}"
        f"{budget_line}"
        f"{dur_line}"
        f"{date_line}"
        f"{rating_line}"
        f"\n~~~~ الوصف ~~~~\n"
        f"{p.get('description','')}\n"
        f"\n🔗 {p['url']}"
    )


# ── Upwork OAuth 2.0 ──────────────────────────────────────────────────────────

UPWORK_TOKEN_URL   = 'https://www.upwork.com/api/v3/oauth2/token'
UPWORK_SEARCH_URL  = 'https://www.upwork.com/api/profiles/v2/search/jobs.json'
UPWORK_REDIRECT    = 'https://www.upwork.com'

def _upwork_refresh():
    """Refresh the Upwork access token and persist to .env and global."""
    global _upwork_access_token, _upwork_refresh_token
    if not _upwork_refresh_token:
        return False
    try:
        resp = requests.post(UPWORK_TOKEN_URL, data={
            'grant_type':    'refresh_token',
            'refresh_token': _upwork_refresh_token,
            'client_id':     UPWORK_CLIENT_ID,
            'client_secret': UPWORK_CLIENT_SECRET,
            'redirect_uri':  UPWORK_REDIRECT,
        }, timeout=15)
        if resp.status_code != 200:
            logger.error(f"Upwork refresh failed: {resp.status_code}")
            return False
        tokens = resp.json()
        _upwork_access_token  = tokens.get('access_token', _upwork_access_token)
        _upwork_refresh_token = tokens.get('refresh_token', _upwork_refresh_token)
        # Persist to .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            import re as _re
            with open(env_path, 'r', encoding='utf-8') as f:
                txt = f.read()
            txt = _re.sub(r'UPWORK_ACCESS_TOKEN=.*',  f'UPWORK_ACCESS_TOKEN={_upwork_access_token}',  txt)
            txt = _re.sub(r'UPWORK_REFRESH_TOKEN=.*', f'UPWORK_REFRESH_TOKEN={_upwork_refresh_token}', txt)
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(txt)
        logger.info("Upwork: تم تجديد الـ token")
        return True
    except Exception as e:
        logger.error(f"Upwork refresh error: {e}")
        return False


def fetch_upwork_jobs():
    """Fetch recent web/dev jobs from Upwork API (OAuth 2.0). Returns {job_id: job_dict}."""
    global _upwork_access_token
    if not all([UPWORK_CLIENT_ID, UPWORK_CLIENT_SECRET, _upwork_access_token]):
        return {}

    def _get(token):
        return requests.get(
            UPWORK_SEARCH_URL,
            headers={'Authorization': f'Bearer {token}'},
            params={
                'q':            'web development programming mobile app',
                'category2_uid': '531770282580668418',
                'sort':         'recency',
                'paging':       '0;20',
            },
            timeout=15,
        )

    try:
        resp = _get(_upwork_access_token)
        if resp.status_code == 401:
            if _upwork_refresh():
                resp = _get(_upwork_access_token)
            else:
                logger.error("Upwork: انتهت صلاحية الـ token — شغّل upwork_auth.py من جديد")
                return {}
        if resp.status_code != 200:
            logger.error(f"Upwork API {resp.status_code}: {resp.text[:200]}")
            return {}

        data     = resp.json()
        jobs_raw = data.get('jobs', {}).get('job', [])
        if isinstance(jobs_raw, dict):
            jobs_raw = [jobs_raw]

        result = {}
        for job in jobs_raw:
            job_id = str(job.get('id', '')).strip()
            if not job_id:
                continue
            budget_obj = job.get('budget', {}) or {}
            if budget_obj.get('amount'):
                budget = f"${budget_obj['amount']}"
            elif budget_obj.get('min') and budget_obj.get('max'):
                budget = f"${budget_obj['min']} - ${budget_obj['max']}"
            else:
                budget = ''
            result[job_id] = {
                'title':       job.get('title', '').strip(),
                'description': (job.get('snippet', '') or '').strip()[:700],
                'budget':      budget,
                'duration':    job.get('duration', ''),
                'date':        (job.get('date_created', '') or '')[:10],
                'url':         f"https://www.upwork.com/jobs/~{job_id}",
            }
        return result
    except Exception as e:
        logger.error(f"Upwork fetch: {e}")
        return {}


def format_upwork(job):
    budget_line   = f"💵 {job['budget']}\n"   if job.get('budget')   else ""
    duration_line = f"⌛ {job['duration']}\n" if job.get('duration') else ""
    date_line     = f"📅 {job['date'][:10]}\n" if job.get('date')    else ""
    return (
        f"🌐 المصدر: upwork.com\n\n"
        f"🎯 {job['title']}\n"
        f"📂 برمجة، تطوير المواقع والتطبيقات\n"
        f"{budget_line}"
        f"{duration_line}"
        f"{date_line}"
        f"\n~~~~ الوصف ~~~~\n"
        f"{job.get('description', '')}\n"
        f"\n🔗 {job['url']}"
    )


def upwork_loop(bot):
    """Separate thread: poll Upwork every SCRAPE_INTERVAL seconds."""
    if not UPWORK_CONSUMER_KEY:
        logger.info("Upwork: بيانات API غير موجودة — تم التخطي")
        return

    # Init: mark existing jobs as seen
    try:
        existing = fetch_upwork_jobs()
        for jid in existing:
            upwork_seen_ids.add(jid)
        save_data()
        logger.info(f"Upwork init: {len(existing)} وظيفة موجودة محفوظة")
    except Exception as e:
        logger.error(f"Upwork init: {e}")

    time.sleep(SCRAPE_INTERVAL)

    while True:
        try:
            jobs = fetch_upwork_jobs()
            new  = {jid: j for jid, j in jobs.items() if jid not in upwork_seen_ids}
            if new:
                logger.info(f"Upwork: {len(new)} وظيفة جديدة")
            for jid, job in new.items():
                try:
                    content  = format_upwork(job)
                    keyboard = job_subscribe_keyboard("2")
                    try:
                        bot.send_message(FREELANCER_CHANNEL_ID, content, reply_markup=keyboard)
                    except Exception as e:
                        logger.error(f"Upwork القناة: {e}")

                    targets = [u for u in users.values()
                               if isinstance(u, dict) and "2" in u.get('categories', [])]
                    sent = failed = 0
                    for u in targets:
                        try:
                            bot.send_message(u['chat_id'], content)
                            sent += 1
                            time.sleep(0.05)
                        except Exception as dm_e:
                            failed += 1
                            logger.warning(f"Upwork DM فشل → {u.get('name','?')}: {dm_e}")

                    logger.info(f"Upwork نُشر {jid} | {sent} نجح / {failed} فشل | {job['title'][:40]}")
                    upwork_seen_ids.add(jid)
                    save_data()
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Upwork خطأ {jid}: {e}")
                    upwork_seen_ids.add(jid)
        except Exception as e:
            logger.error(f"Upwork loop: {e}")

        time.sleep(SCRAPE_INTERVAL)


def scraper_loop(bot):
    logger.info(f"Scraper بدأ — كل {SCRAPE_INTERVAL}s")
    try:
        existing = fetch_listing()
        for pid in existing:
            seen_ids.add(pid)
        save_data()
        logger.info(f"Scraper init: {len(existing)} مشروع موجود محفوظ")
    except Exception as e:
        logger.error(f"Scraper init: {e}")

    time.sleep(SCRAPE_INTERVAL)

    while True:
        try:
            projects = fetch_listing()
            new = {pid: url for pid, url in projects.items() if pid not in seen_ids}
            if new:
                logger.info(f"Scraper: {len(new)} مشروع جديد")
            for pid, url in new.items():
                try:
                    p = scrape_project(url)
                    cat_id = p.get('category_id')
                    if not cat_id or cat_id not in ACTIVE_CATEGORIES:
                        logger.info(f"تخطي #{pid} — تصنيف [{cat_id}] غير مفعّل: {p.get('title','')[:40]}")
                        seen_ids.add(pid)
                        save_data()
                        time.sleep(3)
                        continue

                    content  = format_scraped(p)
                    keyboard = job_subscribe_keyboard(cat_id)

                    # Post to channel
                    try:
                        bot.send_message(FREELANCER_CHANNEL_ID, content, reply_markup=keyboard)
                    except Exception as e:
                        logger.error(f"القناة #{pid}: {e}")

                    # Send DM to subscribed users
                    targets = [u for u in users.values()
                               if isinstance(u, dict) and cat_id in u.get('categories', [])]
                    sent = failed = 0
                    for u in targets:
                        try:
                            bot.send_message(u['chat_id'], content)
                            sent += 1
                            time.sleep(0.05)
                        except Exception as e:
                            failed += 1
                            logger.warning(f"DM فشل → {u.get('name','?')} [{u['chat_id']}]: {e}")

                    cat_name = ALL_CATEGORIES.get(cat_id, cat_id)
                    logger.info(
                        f"نُشر #{pid} [{cat_name}] | إشعارات: {sent} نجح / {failed} فشل"
                        f" | {p['title'][:40]}"
                    )

                    seen_ids.add(pid)
                    save_data()
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"خطأ #{pid}: {e}")
                    seen_ids.add(pid)
        except Exception as e:
            logger.error(f"Scraper: {e}")

        time.sleep(SCRAPE_INTERVAL)


# ── Main dispatcher ───────────────────────────────────────────────────────────

def handle_msg(bot, chat_id, user_id, text, name):
    if user_id not in users:
        users[user_id] = {"name": name, "chat_id": chat_id, "categories": []}
    users[user_id]["chat_id"] = chat_id

    # ── Admin ──
    if user_id == ADMIN_ID:
        if text == "/stats":   admin_stats(bot, chat_id);  return
        if text == "/users":   admin_users(bot, chat_id);  return
        if text == "/menu":    post_channel_menu(bot, chat_id); return
        if text == "/test":    admin_test(bot, chat_id);   return
        if text == "/cancel":
            admin_state.pop(user_id, None)
            bot.send_message(chat_id, "❌ تم الإلغاء."); return
        if text == "/newpost": newpost_start(bot, chat_id, user_id); return
        if text.startswith("/post"):
            admin_post_step1(bot, chat_id, user_id, text); return

        if user_id in admin_state:
            step = admin_state[user_id].get("step", "")
            if step.startswith("np_") and step != "np_confirm":
                newpost_next(bot, chat_id, user_id, text); return
            if step == "np_confirm":
                if text == "✅":
                    newpost_confirm(bot, chat_id, user_id)
                else:
                    bot.send_message(chat_id, "إرسل ✅ للتأكيد أو /cancel للإلغاء.")
                return
            if step == "waiting_content":
                admin_post_step2(bot, chat_id, user_id, text); return

    # ── User ──
    if text == "/start":              handle_start(bot, chat_id, user_id, name);  return
    if text == "/stop":               handle_stop(bot, chat_id, user_id);          return
    if text == "/edit":               handle_edit(bot, chat_id, user_id, name);   return
    if text == "/mystats":            handle_mystats(bot, chat_id, user_id);       return
    if text == "✔️ تأكيد التصنيفات": handle_confirm(bot, chat_id, user_id);       return

    try:
        clean = text.replace("✅ ", "").split('.')[0].strip()
        if clean in ALL_CATEGORIES:
            toggle_category(bot, chat_id, user_id, clean)
    except Exception:
        pass


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global last_id, BOT_USERNAME
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN مفقود!")
        return

    load_data()

    request = Request(connect_timeout=10, read_timeout=10)
    bot = Bot(token=TELEGRAM_TOKEN, request=request)

    try:
        info = bot.get_me()
        BOT_USERNAME = info.username
    except Exception as e:
        print(f"❌ فشل الاتصال: {e}"); return

    print("\n" + "="*60)
    print("✅ البوت يعمل الآن!")
    print(f"🤖 @{BOT_USERNAME}")
    print(f"👤 Admin   : {ADMIN_ID}")
    print(f"👥 مشتركون : {len(users)}")
    print(f"🕒 Scraper : كل {SCRAPE_INTERVAL}s")
    print("="*60)
    print("أوامر الأدمين: /menu  /stats  /users  /post  /newpost")
    print("="*60 + "\n")

    threading.Thread(target=scraper_loop, args=(bot,), daemon=True).start()
    threading.Thread(target=upwork_loop,  args=(bot,), daemon=True).start()
    logger.info("البوت يعمل!")

    ALLOWED_UPDATES = ['message', 'callback_query', 'chat_member']

    while True:
        try:
            updates = bot.get_updates(
                offset=last_id + 1,
                timeout=10,
                allowed_updates=ALLOWED_UPDATES,
            )
            for update in updates:
                last_id = update.update_id

                if update.message and update.message.from_user:
                    msg = update.message
                    handle_msg(bot, msg.chat.id, msg.from_user.id,
                               (msg.text or '').strip(),
                               msg.from_user.first_name or 'صديقي')

                elif update.callback_query:
                    try:
                        handle_callback(bot, update.callback_query)
                    except Exception as e:
                        logger.error(f"callback: {e}")

                elif update.chat_member:
                    try:
                        handle_new_member(bot, update.chat_member)
                    except Exception as e:
                        logger.error(f"chat_member: {e}")

            time.sleep(0.1)
        except Exception as e:
            logger.error(f"خطأ: {e}")
            time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 توقف البوت")
        save_data()
