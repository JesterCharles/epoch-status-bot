import sqlite3
from typing import Optional, List, Tuple

class Database:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_optins (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        try:
            cursor.execute('ALTER TABLE notification_optins ADD COLUMN user_name TEXT')
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    def set_notification_channel(self, guild_id: int, channel_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO guild_settings (guild_id, channel_id) VALUES (?, ?)",
            (guild_id, channel_id)
        )
        conn.commit()
        conn.close()

    def get_notification_channel(self, guild_id: int) -> Optional[int]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None

    def add_optin_user(self, guild_id: int, user_id: int, user_name: Optional[str] = None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO notification_optins (guild_id, user_id, user_name) VALUES (?, ?, ?)",
            (guild_id, user_id, user_name)
        )
        conn.commit()
        conn.close()

    def remove_optin_user(self, guild_id: int, user_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notification_optins WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        conn.commit()
        conn.close()

    def get_optin_users(self, guild_id: int) -> List[Tuple[int, Optional[str]]]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, user_name FROM notification_optins WHERE guild_id = ?",
            (guild_id,)
        )
        users = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return users
