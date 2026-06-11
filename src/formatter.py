from datetime import datetime
from typing import List, Optional, Dict, Any
from src.fetcher import Item

class Formatter:
    """消息格式化器"""

    def __init__(self, include_summary: bool = True, include_source: bool = True,
                 include_category: bool = True, max_items: int = 10):
        self.include_summary = include_summary
        self.include_source = include_source
        self.include_category = include_category
        self.max_items = max_items

    def _clean_text(self, value: str) -> str:
        """清理飞书 Markdown 文本中的异常空白。"""
        return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()

    def _escape_link_text(self, value: str) -> str:
        """转义 Markdown 链接文本，避免标题中的方括号破坏链接。"""
        return self._clean_text(value).replace("[", "\\[").replace("]", "\\]")

    def format_single_item(self, item: Item) -> Dict[str, Any]:
        """格式化单个条目为飞书卡片"""
        elements = []

        # 标题
        title_content = f"**标题**\n[{self._escape_link_text(item.title)}]({item.url})"
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": title_content}
        })

        # 来源和分类
        meta_parts = []
        if self.include_source and item.source:
            meta_parts.append(f"**来源** | {self._clean_text(item.source)}")
        if self.include_category and item.category:
            meta_parts.append(f"**分类** | {self._clean_text(item.category)}")

        if meta_parts:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "    ".join(meta_parts)}
            })

        # 摘要
        if self.include_summary and item.summary:
            summary_content = f"**摘要**\n{self._clean_text(item.summary)}"
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": summary_content}
            })

        # 分隔线
        elements.append({"tag": "hr"})

        # 时间戳
        time_str = item.published_at.strftime("%Y-%m-%d %H:%M")
        elements.append({
            "tag": "note",
            "elements": [{"tag": "plain_text", "content": f"来自 AIHOT | {time_str}"}]
        })

        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": "🔥 AI 热点更新"},
                    "template": "turquoise"
                },
                "elements": elements
            }
        }

    def format_multiple_items(self, items: List[Item]) -> Optional[Dict[str, Any]]:
        """格式化多个条目"""
        if not items:
            return None

        if len(items) == 1:
            return self.format_single_item(items[0])

        # 多条合并格式化
        elements = []

        # 标题
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**共 {len(items)} 条更新**"}
        })

        # 每条内容
        for i, item in enumerate(items[:self.max_items], 1):
            content_parts = [
                f"**{i}.** [{self._escape_link_text(item.title)}]({item.url})"
            ]

            meta_parts = []
            if self.include_source and item.source:
                meta_parts.append(f"来源: {self._clean_text(item.source)}")
            if self.include_category and item.category:
                meta_parts.append(f"分类: {self._clean_text(item.category)}")
            meta_parts.append(f"时间: {item.published_at.strftime('%Y-%m-%d %H:%M')}")

            if meta_parts:
                content_parts.append(" | ".join(meta_parts))
            if self.include_summary and item.summary:
                content_parts.append(self._clean_text(item.summary))

            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "\n".join(content_parts)}
            })

        if len(items) > self.max_items:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"... 还有 {len(items) - self.max_items} 条，请查看网站"}
            })

        # 分隔线
        elements.append({"tag": "hr"})

        # 时间戳
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        elements.append({
            "tag": "note",
            "elements": [{"tag": "plain_text", "content": f"来自 AIHOT | {time_str}"}]
        })

        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"🔥 AI 热点更新 ({len(items)}条)"},
                    "template": "turquoise"
                },
                "elements": elements
            }
        }
