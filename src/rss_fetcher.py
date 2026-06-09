import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
from src.fetcher import Item


class RSSFetcher:
    """RSS 抓取器"""

    def __init__(self, rss_url: str):
        self.rss_url = rss_url

    def fetch_items(self, since: Optional[datetime] = None) -> List[Item]:
        """获取 RSS 中的条目"""
        try:
            response = requests.get(self.rss_url, timeout=30)
            if response.status_code != 200:
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
                            pub_date = datetime.utcnow()
                    else:
                        pub_date = datetime.utcnow()

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

                except Exception:
                    continue

            return items

        except Exception:
            return []
