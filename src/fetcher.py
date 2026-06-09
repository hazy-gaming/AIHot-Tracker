import requests
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Item:
    """AI 新闻条目数据类"""
    id: str
    title: str
    url: str
    summary: Optional[str]
    category: Optional[str]
    source: Optional[str]
    published_at: datetime


class Fetcher:
    """AIHOT API 客户端"""

    def __init__(self, api_url: str):
        self.api_url = api_url

    def fetch_items(self, since: datetime) -> List[Item]:
        """获取指定时间之后的条目"""
        try:
            params = {
                "mode": "selected",
                "since": since.isoformat()
            }

            response = requests.get(self.api_url, params=params, timeout=30)

            if response.status_code != 200:
                return []

            data = response.json()
            items = []

            for item_data in data.get("items", []):
                try:
                    published_at = datetime.fromisoformat(
                        item_data.get("published_at", "").replace("Z", "+00:00")
                    )
                    item = Item(
                        id=item_data["id"],
                        title=item_data["title"],
                        url=item_data["url"],
                        summary=item_data.get("summary"),
                        category=item_data.get("category"),
                        source=item_data.get("source"),
                        published_at=published_at
                    )
                    items.append(item)
                except (KeyError, ValueError):
                    continue

            return items

        except Exception:
            return []
