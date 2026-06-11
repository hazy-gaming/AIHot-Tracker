from abc import ABC, abstractmethod
from typing import List
from src.fetcher import Item


class BasePusher(ABC):
    """推送基类"""

    @abstractmethod
    def push(self, items: List[Item]) -> bool:
        """推送条目"""
        ...
