"""
قاعدة بيانات البوت لتخزين المستخدمين والمشاريع التي تم إرسالها
"""
import sqlite3
import json
from datetime import datetime
import os

DATABASE_PATH = './data/bot_data.db'

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                categories TEXT,
                created_at TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # جدول المشاريع المرسلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_projects (
                project_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                category TEXT,
                url TEXT,
                sent_at TIMESTAMP,
                user_id INTEGER
            )
        ''')

        # جدول تاريخ المشاريع المكتشفة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS last_check (
                category TEXT PRIMARY KEY,
                last_project_id TEXT,
                last_check_time TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id, username, categories):
        """إضافة مستخدم جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users
                (user_id, username, categories, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (user_id, username, json.dumps(categories), datetime.now()))

            conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في إضافة المستخدم: {e}")
            return False
        finally:
            conn.close()

    def get_user_categories(self, user_id):
        """الحصول على التصنيفات المختارة من قبل المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT categories FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return []
        except Exception as e:
            print(f"خطأ في الحصول على تصنيفات المستخدم: {e}")
            return []
        finally:
            conn.close()

    def save_sent_project(self, project_id, title, description, category, url, user_id):
        """حفظ مشروع تم إرساله"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO sent_projects
                (project_id, title, description, category, url, sent_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (project_id, title, description, category, url, datetime.now(), user_id))

            conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في حفظ المشروع: {e}")
            return False
        finally:
            conn.close()

    def get_all_active_users(self):
        """الحصول على جميع المستخدمين النشطين"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT user_id, categories FROM users WHERE is_active = 1')
            results = cursor.fetchall()
            return [(row[0], json.loads(row[1])) for row in results]
        except Exception as e:
            print(f"خطأ في الحصول على المستخدمين: {e}")
            return []
        finally:
            conn.close()

    def deactivate_user(self, user_id):
        """تعطيل حساب المستخدم"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في تعطيل المستخدم: {e}")
            return False
        finally:
            conn.close()

