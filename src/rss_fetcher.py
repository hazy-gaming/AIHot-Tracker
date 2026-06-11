import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional
from src.fetcher import Item

logger = logging.getLogger(__name__)


class RSSFetcher:
    """RSS 抓取器"""

    HEADERS = {
        "User-Agent": "AIHOT-Tracker/1.0"
    }

    def __init__(self, rss_url: str):
        self.rss_url = rss_url

    def fetch_items(self, since: Optional[datetime] = None) -> List[Item]:
        """获取 RSS 中的条目"""
        try:
            response = requests.get(self.rss_url, headers=self.HEADERS, timeout=30)
            if response.status_code != 200:
                logger.warning(f"RSS 返回非 200 状态码: {response.status_code}")
                return []

            # 解析 XML
            root = ET.fromstring(response.content)
            items = []

            for item_elem in root.findall('.//item'):
                try:
                    # 提取信息
                    title = item_elem.findtext('title', '')
                    link = item_elem.findtext('link', '')
                    description = item_elem.findtext('description', '')
                    pub_date_str = item_elem.findtext('pubDate', '')
                    guid = item_elem.findtext('guid', '')
                    author = item_elem.findtext('author', '')

                    # 解析发布时间
                    if pub_date_str:
                        # RSS 日期格式: "Tue, 09 Jun 2026 19:38:28 GMT"
                        try:
                            pub_date = datetime.strptime(
                                pub_date_str, '%a, %d %b %Y %H:%M:%S %Z'
                            )
                        except ValueError:
                            logger.debug(f"无法解析 RSS 日期: {pub_date_str}")
                            pub_date = datetime.now(timezone.utc)
                    else:
                        pub_date = datetime.now(timezone.utc)

                    # 过滤时间
                    if since and pub_date < since:
                        continue

                    # 提取分类和来源
                    category = None
                    source = None
                    if author:
                        # author 格式: "noreply@aihot.virxact.com (Hugging Face：Blog（RSS）)"
                        if '(' in author and ')' in author:
                            source = author.split('(')[1].rstrip(')')

                    item = Item(
                        id=guid or link,
                        title=title,
                        url=link,
                        summary=description,
                        category=category,
                        source=source,
                        published_at=pub_date
                    )
                    items.append(item)

                except Exception as e:
                    logger.debug(f"解析 RSS 条目失败: {e}")
                    continue

            return items

        except Exception as e:
            logger.error(f"获取 RSS 条目失败: {e}")
            return []
