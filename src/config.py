import os
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv

class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        load_dotenv()

        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    @property
    def source_api_url(self) -> str:
        return self._config.get('source', {}).get('api_url',
            'https://aihot.virxact.com/api/public/items')

    @property
    def source_default_mode(self) -> str:
        return self._config.get('source', {}).get('default_mode', 'selected')

    @property
    def source_default_category(self) -> Optional[str]:
        return self._config.get('source', {}).get('default_category')

    @property
    def polling_base_interval(self) -> int:
        return self._config.get('polling', {}).get('base_interval', 300)

    @property
    def polling_min_interval(self) -> int:
        return self._config.get('polling', {}).get('min_interval', 60)

    @property
    def polling_max_interval(self) -> int:
        return self._config.get('polling', {}).get('max_interval', 900)

    @property
    def polling_empty_threshold(self) -> int:
        return self._config.get('polling', {}).get('empty_threshold', 3)

    @property
    def polling_work_hours_start(self) -> int:
        return self._config.get('polling', {}).get('work_hours', {}).get('start', 9)

    @property
    def polling_work_hours_end(self) -> int:
        return self._config.get('polling', {}).get('work_hours', {}).get('end', 18)

    @property
    def polling_work_hours_interval(self) -> int:
        return self._config.get('polling', {}).get('work_hours', {}).get('interval', 300)

    @property
    def polling_off_hours_interval(self) -> int:
        return self._config.get('polling', {}).get('off_hours_interval', 900)

    @property
    def feishu_webhook_url(self) -> str:
        return os.getenv('FEISHU_WEBHOOK_URL',
            self._config.get('push', {}).get('channels', {}).get('feishu', {}).get('webhook_url', ''))

    @property
    def feishu_webhook_secret(self) -> str:
        return os.getenv('FEISHU_WEBHOOK_SECRET',
            self._config.get('push', {}).get('channels', {}).get('feishu', {}).get('secret', ''))

    @property
    def feishu_enabled(self) -> bool:
        return self._config.get('push', {}).get('channels', {}).get('feishu', {}).get('enabled', True)

    @property
    def message_max_items(self) -> int:
        return self._config.get('message', {}).get('max_items_per_message', 10)

    @property
    def message_merge_threshold(self) -> int:
        return self._config.get('message', {}).get('merge_threshold', 3)

    @property
    def message_include_summary(self) -> bool:
        return self._config.get('message', {}).get('include_summary', True)

    @property
    def message_include_source(self) -> bool:
        return self._config.get('message', {}).get('include_source', True)

    @property
    def message_include_category(self) -> bool:
        return self._config.get('message', {}).get('include_category', True)

    @property
    def storage_db_path(self) -> str:
        return self._config.get('storage', {}).get('db_path', './data/aihot_tracker.db')

    @property
    def storage_log_path(self) -> str:
        return self._config.get('storage', {}).get('log_path', './logs/aihot_tracker.log')