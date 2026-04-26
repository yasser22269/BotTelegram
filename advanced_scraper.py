"""
ملف تجميع Advanced Scraper لموقع مستقل
يستخدم Selenium للتعامل مع المحتوى الديناميكي
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MustaqbalScraper:
    def __init__(self):
        self.base_url = "https://www.mustaqbal.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.last_project_ids = {}

    def get_projects_by_category(self, category_id: str, limit: int = 10) -> list:
        """
        جلب المشاريع من تصنيف معين

        Args:
            category_id: معرّف التصنيف
            limit: عدد المشاريع المراد جلبها

        Returns:
            قائمة بالمشاريع
        """
        try:
            # محاولة الجلب عبر requests أولاً
            url = f"{self.base_url}/projects"
            params = {
                'category': category_id,
                'sort': 'newest'
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                logger.error(f"خطأ في جلب الصفحة: {response.status_code}")
                return []

            projects = self._parse_projects(response.text, category_id)
            return projects[:limit]

        except Exception as e:
            logger.error(f"خطأ في جلب المشاريع: {e}")
            return []

    def _parse_projects(self, html: str, category_id: str) -> list:
        """تحليل صفحة HTML واستخراج المشاريع"""
        soup = BeautifulSoup(html, 'html.parser')
        projects = []

        try:
            # البحث عن عناصر المشاريع
            # هذا يعتمد على البنية الفعلية لموقع مستقل
            project_elements = soup.find_all('div', class_='project-item')

            for element in project_elements:
                try:
                    project = self._extract_project_data(element, category_id)
                    if project:
                        projects.append(project)
                except Exception as e:
                    logger.warning(f"خطأ في استخراج بيانات المشروع: {e}")
                    continue

        except Exception as e:
            logger.error(f"خطأ في تحليل HTML: {e}")

        return projects

    def _extract_project_data(self, element, category_id: str) -> dict:
        """استخراج بيانات مشروع واحد"""
        try:
            # استخراج معرّف المشروع
            project_id = element.get('data-project-id', '')

            # استخراج العنوان
            title_elem = element.find('h3', class_='project-title')
            title = title_elem.get_text(strip=True) if title_elem else 'بدون عنوان'

            # استخراج الوصف
            desc_elem = element.find('p', class_='project-description')
            description = desc_elem.get_text(strip=True) if desc_elem else ''

            # استخراج الميزانية
            budget_elem = element.find('span', class_='budget')
            budget = budget_elem.get_text(strip=True) if budget_elem else 'غير محدد'

            # استخراج مستوى المشروع
            level_elem = element.find('span', class_='level')
            level = level_elem.get_text(strip=True) if level_elem else 'عام'

            # استخراج الرابط
            link_elem = element.find('a', class_='project-link')
            url = link_elem.get('href', '') if link_elem else ''
            if url and not url.startswith('http'):
                url = self.base_url + url

            # استخراج التاريخ
            date_elem = element.find('span', class_='posted-date')
            posted_date = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()

            return {
                'id': project_id,
                'title': title,
                'description': description,
                'budget': budget,
                'level': level,
                'url': url,
                'category_id': category_id,
                'posted_date': posted_date,
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"خطأ في استخراج بيانات المشروع: {e}")
            return None

    def get_new_projects(self, category_id: str) -> list:
        """
        جلب المشاريع الجديدة فقط منذ آخر فحص
        """
        current_projects = self.get_projects_by_category(category_id, limit=20)

        last_id = self.last_project_ids.get(category_id)

        new_projects = []
        for project in current_projects:
            if last_id is None:
                # الفحص الأول
                new_projects.append(project)
            elif project['id'] != last_id:
                new_projects.append(project)
            else:
                # وجدنا آخر مشروع معروف، توقف هنا
                break

        # تحديث معرّف آخر مشروع
        if current_projects:
            self.last_project_ids[category_id] = current_projects[0]['id']

        return new_projects


# مثال الاستخدام
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = MustaqbalScraper()

    # جلب المشاريع من التصنيف الأول (البرمجة)
    projects = scraper.get_projects_by_category("1", limit=5)

    print("المشاريع الحالية:")
    for project in projects:
        print(f"\n- {project['title']}")
        print(f"  الميزانية: {project['budget']}")
        print(f"  الرابط: {project['url']}")

