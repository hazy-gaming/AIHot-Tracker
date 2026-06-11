import logging
import requests
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


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

    HEADERS = {
        "User-Agent": "AIHOT-Tracker/1.0"
    }

    def __init__(self, api_url: str, mode: str = "selected"):
        self.api_url = api_url
        self.mode = mode

    def fetch_items(self, since: datetime) -> List[Item]:
        """获取指定时间之后的条目"""
        try:
            # API 要求 Z 格式（UTC），而非 +00:00
            since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
            params = {
                "mode": self.mode,
                "since": since_str
            }

            response = requests.get(self.api_url, params=params, headers=self.HEADERS, timeout=30)

            if response.status_code != 200:
                logger.warning(f"API 返回非 200 状态码: {response.status_code}")
                return []

            data = response.json()
            items = []

            for item_data in data.get("items", []):
                try:
                    # 只处理精选条目（selected=True）
                    if not item_data.get("selected", False):
                        continue

                    # API 返回 publishedAt（驼峰），兼容 published_at（下划线）
                    published_str = item_data.get("publishedAt") or item_data.get("published_at", "")
                    published_at = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
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
                except (KeyError, ValueError) as e:
                    logger.debug(f"解析条目失败: {e}")
                    continue

            return items

        except Exception as e:
            logger.error(f"获取条目失败: {e}")
            return []
