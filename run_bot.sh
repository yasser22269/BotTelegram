#!/bin/bash
# بوت مستقل - ملف التشغيل لـ Linux/macOS

echo ""
echo "================================================"
echo "بوت مستقل - Mustaqbal Bot"
echo "================================================"
echo ""

# الذهاب إلى مجلد البوت
cd "$(dirname "$0")"

# التحقق من وجود Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 غير مثبت"
    echo "[INFO] قم بتثبيت Python 3 أولاً"
    exit 1
fi

# التحقق من وجود ملف .env
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] ملف .env غير موجود!"
    echo "[INFO] سيتم نسخه من .env.example"
    echo ""
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "[OK] تم إنشاء ملف .env"
        echo ""
        echo "[WARNING] قم بتحرير ملف .env وأدخل بيانات البوت الخاصة بك"
        echo "[INFO] خاصة: TELEGRAM_TOKEN و ADMIN_ID"
        echo ""
        read -p "اضغط Enter للمتابعة..."
    else
        echo "[ERROR] ملف .env.example غير موجود!"
        exit 1
    fi
fi

# تثبيت المتطلبات
echo "[INFO] جاري التحقق من المتطلبات..."
pip3 install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "[ERROR] فشل تثبيت المتطلبات"
    exit 1
fi

echo ""
echo "================================================"
echo "تشغيل البوت..."
echo "================================================"
echo ""

python3 bot.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] حدث خطأ في البوت"
    exit 1
fi

