"""
سكريبت تجميع بيانات التصنيفات من موقع مستقل
"""
import requests
from bs4 import BeautifulSoup
import json

def scrape_categories():
    """تجميع التصنيفات المتاحة من موقع مستقل"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        url = "https://www.mustaqbal.com/projects"
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.content, 'html.parser')

        # هنا نبحث عن عناصر التصنيفات
        # هذا يعتمد على البنية الفعلية للموقع
        categories = {}

        # محاولة إيجاد قائمة التصنيفات
        category_elements = soup.find_all('a', class_='category-item')

        for idx, elem in enumerate(category_elements, 1):
            category_name = elem.get_text(strip=True)
            categories[str(idx)] = category_name

        return categories

    except Exception as e:
        print(f"خطأ في تجميع التصنيفات: {e}")
        return {}


# التصنيفات الافتراضية (يمكن تحديثها من الموقع)
DEFAULT_CATEGORIES = {
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

if __name__ == "__main__":
    categories = scrape_categories()
    if not categories:
        categories = DEFAULT_CATEGORIES

    print("التصنيفات المتاحة:")
    for key, value in categories.items():
        print(f"{key}. {value}")

    # حفظ التصنيفات
    with open('categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

    print("\nتم حفظ التصنيفات في categories.json")

