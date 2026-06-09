from typing import List
from src.fetcher import Item

class BasePusher:
    """推送基类"""

    def push(self, items: List[Item]) -> bool:
        """推送条目"""
        raise NotImplementedError
