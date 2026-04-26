@echo off
REM بوت مستقل - ملف التشغيل
REM This batch file starts the Mustaqbal Bot

echo.
echo ================================================
echo بوت مستقل - Mustaqbal Bot
echo ================================================
echo.

cd /d "%~dp0"

REM التحقق من وجود Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python غير مثبت أو غير مسجل في PATH
    echo [ERROR] Please install Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM التحقق من وجود ملف .env
if not exist ".env" (
    echo.
    echo [WARNING] ملف .env غير موجود!
    echo [INFO] سيتم نسخه من .env.example
    echo.
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo [OK] تم إنشاء ملف .env
        echo.
        echo [WARNING] قم بتحرير ملف .env وأدخل بيانات البوت الخاصة بك
        echo [INFO] خاصة: TELEGRAM_TOKEN و ADMIN_ID
        echo.
        pause
    ) else (
        echo [ERROR] ملف .env.example غير موجود!
        pause
        exit /b 1
    )
)

REM تثبيت المتطلبات
echo [INFO] جاري التحقق من المتطلبات...
pip install -q -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] فشل تثبيت المتطلبات
    pause
    exit /b 1
)

echo.
echo ================================================
echo تشغيل البوت...
echo ================================================
echo.

python bot.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] حدث خطأ في البوت
    pause
    exit /b 1
)

pause

