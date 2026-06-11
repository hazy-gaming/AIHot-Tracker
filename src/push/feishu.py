import time
import hashlib
import hmac
import base64
import requests
from typing import List
from src.push.base import BasePusher
from src.fetcher import Item
from src.formatter import Formatter

class FeishuPusher(BasePusher):
    """飞书推送器"""

    def __init__(self, webhook_url: str, secret: str = "",
                 include_summary: bool = True, include_source: bool = True,
                 include_category: bool = True, max_items: int = 10):
        self.webhook_url = webhook_url
        self.secret = secret
        self.formatter = Formatter(
            include_summary=include_summary,
            include_source=include_source,
            include_category=include_category,
            max_items=max_items
        )

    def _generate_sign(self, timestamp: str) -> str:
        """生成飞书签名"""
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    def push(self, items: List[Item]) -> bool:
        """推送到飞书"""
        if not items:
            return True

        try:
            message = self.formatter.format_multiple_items(items)
            if message is None:
                return True

            # 添加签名（如果配置了 secret）
            if self.secret:
                timestamp = str(int(time.time()))
                sign = self._generate_sign(timestamp)
                message["timestamp"] = timestamp
                message["sign"] = sign

            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("code") == 0

            return False

        except Exception:
            return False
