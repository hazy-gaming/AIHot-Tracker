import sqlite3
from datetime import datetime
from typing import Optional

class Database:
    """SQLite 数据库管理类"""

    def __init__(self, db_path: str):
        self.path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pushed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    summary TEXT,
                    category TEXT,
                    source TEXT,
                    pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS push_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    items_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS poll_state (
                    id INTEGER PRIMARY KEY,
                    last_poll_at TIMESTAMP,
                    last_new_item_at TIMESTAMP,
                    consecutive_empty INTEGER DEFAULT 0,
                    current_interval INTEGER DEFAULT 300
                )
            """)

            # 初始化轮询状态（如果不存在）
            conn.execute("""
                INSERT OR IGNORE INTO poll_state (id, consecutive_empty, current_interval)
                VALUES (1, 0, 300)
            """)

            conn.commit()

    def item_exists(self, item_id: str) -> bool:
        """检查条目是否已存在"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT EXISTS(SELECT 1 FROM pushed_items WHERE item_id = ?)",
                (item_id,)
            )
            return bool(cursor.fetchone()[0])

    def insert_item(self, item_id: str, title: str, url: str,
                    summary: Optional[str], category: Optional[str],
                    source: Optional[str]) -> bool:
        """插入新条目"""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """INSERT INTO pushed_items (item_id, title, url, summary, category, source)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (item_id, title, url, summary, category, source)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False

    def get_last_poll_time(self) -> Optional[datetime]:
        """获取上次轮询时间"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT last_poll_at FROM poll_state WHERE id = 1"
            )
            row = cursor.fetchone()
            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None

    def update_poll_state(self, poll_time: datetime):
        """更新轮询状态"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET last_poll_at = ? WHERE id = 1",
                (poll_time.isoformat(),)
            )
            conn.commit()

    def get_consecutive_empty(self) -> int:
        """获取连续空轮询次数"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT consecutive_empty FROM poll_state WHERE id = 1"
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    def update_consecutive_empty(self, count: int):
        """更新连续空轮询次数"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET consecutive_empty = ? WHERE id = 1",
                (count,)
            )
            conn.commit()

    def get_current_interval(self) -> int:
        """获取当前轮询间隔"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT current_interval FROM poll_state WHERE id = 1"
            )
            row = cursor.fetchone()
            return row[0] if row else 300

    def update_current_interval(self, interval: int):
        """更新当前轮询间隔"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET current_interval = ? WHERE id = 1",
                (interval,)
            )
            conn.commit()

    def update_last_new_item_time(self, item_time: datetime):
        """更新上次发现新内容时间"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET last_new_item_at = ? WHERE id = 1",
                (item_time.isoformat(),)
            )
            conn.commit()

    def log_push(self, channel: str, status: str,
                 error_message: Optional[str] = None,
                 items_count: int = 0) -> bool:
        """记录推送日志"""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """INSERT INTO push_logs (channel, status, error_message, items_count)
                       VALUES (?, ?, ?, ?)""",
                    (channel, status, error_message, items_count)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False
