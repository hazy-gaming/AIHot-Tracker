import time
import logging
import requests
from typing import List, Optional, Dict

from src.fetcher import Item

logger = logging.getLogger(__name__)


class FeishuBitableWriter:
    """飞书多维表格写入器"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    RECORDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

    DEFAULT_FIELD_MAPPING = {
        "title": "标题",
        "url": "链接",
        "summary": "摘要",
        "category": "分类",
        "source": "来源",
        "published_at": "发布时间",
    }

    def __init__(self, app_id: str, app_secret: str, app_token: str, table_id: str,
                 field_mapping: Optional[Dict[str, str]] = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.field_mapping = field_mapping or self.DEFAULT_FIELD_MAPPING

        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_tenant_access_token(self) -> Optional[str]:
        """获取 tenant_access_token，带缓存自动刷新"""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        try:
            resp = requests.post(self.TOKEN_URL, json={
                "app_id": self.app_id,
                "app_secret": self.app_secret,
            }, timeout=10)

            if resp.status_code != 200:
                logger.error(f"获取 tenant_access_token 失败: HTTP {resp.status_code}")
                return None

            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"获取 tenant_access_token 失败: {data.get('msg')}")
                return None

            self._token = data["tenant_access_token"]
            # 提前 5 分钟过期，避免边界问题
            self._token_expires_at = time.time() + data.get("expire", 7200) - 300
            logger.info("tenant_access_token 获取成功")
            return self._token

        except Exception as e:
            logger.error(f"获取 tenant_access_token 异常: {e}")
            return None

    def _item_to_fields(self, item: Item) -> Dict[str, str]:
        """将 Item 转换为多维表格字段"""
        fields = {}
        for item_attr, bitable_field in self.field_mapping.items():
            value = getattr(item, item_attr, None)
            if value is not None:
                # 时间格式化为字符串
                if item_attr == "published_at":
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                fields[bitable_field] = value
        return fields

    def write(self, items: List[Item]) -> bool:
        """批量写入记录到多维表格"""
        if not items:
            return True

        token = self._get_tenant_access_token()
        if not token:
            return False

        records = [{"fields": self._item_to_fields(item)} for item in items]
        url = self.RECORDS_URL.format(
            app_token=self.app_token,
            table_id=self.table_id,
        )

        try:
            resp = requests.post(url, json={"records": records}, headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }, timeout=15)

            if resp.status_code != 200:
                logger.error(f"写入多维表格失败: HTTP {resp.status_code}")
                return False

            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"写入多维表格失败: {data.get('msg')}")
                return False

            logger.info(f"成功写入 {len(records)} 条记录到多维表格")
            return True

        except Exception as e:
            logger.error(f"写入多维表格异常: {e}")
            return False
