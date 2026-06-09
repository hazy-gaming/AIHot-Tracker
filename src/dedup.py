from typing import List
from src.database import Database
from src.fetcher import Item

class DedupManager:
    """去重管理器"""

    def __init__(self, db: Database):
        self.db = db

    def filter_new_items(self, items: List[Item]) -> List[Item]:
        """过滤出新条目"""
        new_items = []
        for item in items:
            if not self.db.item_exists(item.id):
                new_items.append(item)
        return new_items

    def mark_as_pushed(self, item: Item) -> bool:
        """标记条目为已推送"""
        return self.db.insert_item(
            item_id=item.id,
            title=item.title,
            url=item.url,
            summary=item.summary,
            category=item.category,
            source=item.source
        )
