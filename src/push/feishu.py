import requests
from typing import List
from src.push.base import BasePusher
from src.fetcher import Item
from src.formatter import Formatter

class FeishuPusher(BasePusher):
    """飞书推送器"""

    def __init__(self, webhook_url: str, secret: str = ""):
        self.webhook_url = webhook_url
        self.secret = secret
        self.formatter = Formatter()

    def push(self, items: List[Item]) -> bool:
        """推送到飞书"""
        if not items:
            return True

        try:
            message = self.formatter.format_multiple_items(items)
            if message is None:
                return True

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
