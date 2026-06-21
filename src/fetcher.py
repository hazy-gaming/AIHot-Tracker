import logging
import requests
from datetime import datetime, timezone
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
    published_at: Optional[datetime]
    # 扩展字段（来自 API，可选）
    title_en: Optional[str] = None
    score: Optional[int] = None
    permalink: Optional[str] = None


class Fetcher:
    """AIHOT API 客户端（支持分页 + ETag 缓存）"""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://aihot.virxact.com/"
    }

    def __init__(self, api_url: str, mode: str = "selected", take: int = 100):
        self.api_url = api_url
        self.mode = mode
        self.take = min(max(take, 1), 100)  # API 限制 1-100
        self._etag: Optional[str] = None

    def fetch_items(self, since: datetime) -> List[Item]:
        """获取指定时间之后的条目（自动分页）"""
        try:
            since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

            all_items: List[Item] = []
            cursor: Optional[str] = None

            while True:
                params = {
                    "mode": self.mode,
                    "since": since_str,
                    "take": self.take,
                }
                if cursor:
                    params["cursor"] = cursor

                headers = dict(self.HEADERS)
                if self._etag:
                    headers["If-None-Match"] = self._etag

                response = requests.get(
                    self.api_url, params=params, headers=headers, timeout=30
                )

                # 304 = 无新内容
                if response.status_code == 304:
                    logger.info("ETag 304，无新内容")
                    return []

                if response.status_code != 200:
                    # 尝试解析 400 等错误的详细信息
                    try:
                        err_body = response.json()
                        err_msg = err_body.get("error", response.text)
                    except Exception:
                        err_msg = response.text
                    logger.warning(
                        f"API 返回非 200 状态码: {response.status_code}, 原因: {err_msg}"
                    )
                    return []

                # 只保存首页 ETag（ETag 跟 query 1:1 绑定，分页后续页的 ETag 不能用于首页）
                if cursor is None:
                    etag = response.headers.get("ETag")
                    if etag:
                        self._etag = etag

                data = response.json()

                for item_data in data.get("items", []):
                    try:
                        # all 模式返回混合列表，仍需要二次过滤精选项
                        if self.mode != "selected" and not item_data.get("selected", False):
                            continue

                        # publishedAt 可能为 null，使用当前 UTC 时间作为兜底
                        published_str = (
                            item_data.get("publishedAt")
                            or item_data.get("published_at")
                        )
                        if published_str:
                            published_at = datetime.fromisoformat(
                                published_str.replace("Z", "+00:00")
                            )
                        else:
                            published_at = datetime.now(timezone.utc)

                        item = Item(
                            id=item_data["id"],
                            title=item_data["title"],
                            url=item_data["url"],
                            summary=item_data.get("summary"),
                            category=item_data.get("category"),
                            source=item_data.get("source"),
                            published_at=published_at,
                            title_en=item_data.get("title_en"),
                            score=item_data.get("score"),
                            permalink=item_data.get("permalink"),
                        )
                        all_items.append(item)
                    except (KeyError, ValueError) as e:
                        logger.debug(f"解析条目失败: {e}")
                        continue

                # 分页：检查是否还有下一页
                if data.get("hasNext") and data.get("nextCursor"):
                    cursor = data["nextCursor"]
                    logger.debug(f"翻页，cursor={cursor[:20]}...")
                else:
                    break

            logger.info(f"共获取 {len(all_items)} 个条目（含分页）")
            return all_items

        except Exception as e:
            logger.error(f"获取条目失败: {e}")
            return []
