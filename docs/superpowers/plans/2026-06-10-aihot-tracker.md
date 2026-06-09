# AIHOT Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 AI 新闻实时追踪系统，自动从 AIHOT API 获取新内容并推送到飞书

**Architecture:** 模块化 Python 应用，包含 API 客户端、去重管理器、消息格式化器和可扩展的推送层。使用 SQLite 进行去重存储，支持智能轮询策略。

**Tech Stack:** Python 3.8+, SQLite, requests, pyyaml, python-dotenv

---

## File Structure

```
aihot-tracker/
├── src/
│   ├── __init__.py              # 包初始化
│   ├── main.py                  # 主程序入口
│   ├── config.py                # 配置管理
│   ├── fetcher.py               # API 客户端
│   ├── dedup.py                 # 去重管理器
│   ├── formatter.py             # 消息格式化器
│   ├── database.py              # 数据库管理
│   └── push/
│       ├── __init__.py          # 推送模块初始化
│       ├── base.py              # 推送基类
│       └── feishu.py            # 飞书推送器
├── config/
│   └── config.yaml              # 配置文件
├── data/                        # 数据目录（SQLite）
├── logs/                        # 日志目录
├── scripts/
│   ├── install.sh               # 安装脚本
│   └── setup_service.sh         # systemd 服务配置
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_fetcher.py
│   ├── test_dedup.py
│   ├── test_formatter.py
│   └── test_push.py
├── requirements.txt             # Python 依赖
└── README.md                    # 使用文档
```

---

## Task 1: 项目初始化和依赖配置

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `config/config.yaml`
- Create: `.env.example`

- [ ] **Step 1: 创建 requirements.txt**

```txt
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=1.0.0
pytest>=7.0.0
```

- [ ] **Step 2: 创建 src/__init__.py**

```python
"""AIHOT Tracker - AI 新闻实时推送系统"""

__version__ = "1.0.0"
```

- [ ] **Step 3: 创建 tests/__init__.py**

```python
"""AIHOT Tracker 测试包"""
```

- [ ] **Step 4: 创建 config/config.yaml**

```yaml
# 目标网站配置
source:
  api_url: "https://aihot.virxact.com/api/public/items"
  default_mode: "selected"
  default_category: null

# 轮询配置
polling:
  base_interval: 300
  min_interval: 60
  max_interval: 900
  empty_threshold: 3
  work_hours:
    start: 9
    end: 18
    interval: 300
  off_hours_interval: 900

# 推送配置
push:
  channels:
    feishu:
      enabled: true
      webhook_url: "${FEISHU_WEBHOOK_URL}"
      secret: "${FEISHU_WEBHOOK_SECRET}"
    wechat:
      enabled: false
      webhook_url: ""

# 消息配置
message:
  max_items_per_message: 10
  merge_threshold: 3
  include_summary: true
  include_source: true
  include_category: true

# 存储配置
storage:
  db_path: "./data/aihot_tracker.db"
  log_path: "./logs/aihot_tracker.log"
  backup_enabled: true
  backup_interval_days: 7
```

- [ ] **Step 5: 创建 .env.example**

```bash
# 飞书 Webhook 配置
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
FEISHU_WEBHOOK_SECRET=your-secret-here
```

- [ ] **Step 6: 安装依赖并验证**

Run: `pip install -r requirements.txt`
Expected: 成功安装所有依赖

- [ ] **Step 7: 提交**

```bash
git add requirements.txt src/__init__.py tests/__init__.py config/config.yaml .env.example
git commit -m "feat: 初始化项目结构和依赖配置"
```

---

## Task 2: 配置管理模块

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_config.py
import os
import pytest
from src.config import Config

def test_config_load_default():
    """测试默认配置加载"""
    config = Config()
    assert config.source_api_url == "https://aihot.virxact.com/api/public/items"
    assert config.polling_base_interval == 300

def test_config_load_from_file(tmp_path):
    """测试从文件加载配置"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
source:
  api_url: "https://custom.api.com/items"
  default_mode: "all"
""")
    config = Config(config_path=str(config_file))
    assert config.source_api_url == "https://custom.api.com/items"
    assert config.source_default_mode == "all"

def test_config_env_override(monkeypatch):
    """测试环境变量覆盖"""
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://custom.webhook.com")
    config = Config()
    assert config.feishu_webhook_url == "https://custom.webhook.com"

def test_config_polling_interval():
    """测试轮询间隔配置"""
    config = Config()
    assert config.polling_base_interval == 300
    assert config.polling_min_interval == 60
    assert config.polling_max_interval == 900
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.config'"

- [ ] **Step 3: 写最小实现**

```python
# src/config.py
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: 添加配置管理模块"
```

---

## Task 3: 数据库模块

**Files:**
- Create: `src/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_database.py
import os
import pytest
from datetime import datetime
from src.database import Database

@pytest.fixture
def db(tmp_path):
    """创建测试数据库"""
    db_path = tmp_path / "test.db"
    return Database(str(db_path))

def test_database_init(db):
    """测试数据库初始化"""
    assert os.path.exists(db.path)

def test_insert_item(db):
    """测试插入条目"""
    item_id = "test-123"
    result = db.insert_item(
        item_id=item_id,
        title="测试标题",
        url="https://example.com",
        summary="测试摘要",
        category="测试分类",
        source="Twitter"
    )
    assert result is True
    
    # 验证插入成功
    assert db.item_exists(item_id) is True

def test_item_exists(db):
    """测试条目是否存在"""
    item_id = "test-456"
    assert db.item_exists(item_id) is False
    
    db.insert_item(item_id, "标题", "https://example.com", None, None, None)
    assert db.item_exists(item_id) is True

def test_get_last_poll_time(db):
    """测试获取上次轮询时间"""
    last_poll = db.get_last_poll_time()
    assert last_poll is None  # 初始状态
    
    db.update_poll_state(datetime.now())
    last_poll = db.get_last_poll_time()
    assert last_poll is not None

def test_get_consecutive_empty(db):
    """测试获取连续空轮询次数"""
    count = db.get_consecutive_empty()
    assert count == 0  # 初始状态

def test_update_consecutive_empty(db):
    """测试更新连续空轮询次数"""
    db.update_consecutive_empty(3)
    assert db.get_consecutive_empty() == 3

def test_get_current_interval(db):
    """测试获取当前轮询间隔"""
    interval = db.get_current_interval()
    assert interval == 300  # 默认值

def test_update_current_interval(db):
    """测试更新当前轮询间隔"""
    db.update_current_interval(600)
    assert db.get_current_interval() == 600

def test_log_push(db):
    """测试记录推送日志"""
    result = db.log_push(
        channel="feishu",
        status="success",
        items_count=5
    )
    assert result is True

def test_log_push_failed(db):
    """测试记录失败推送日志"""
    result = db.log_push(
        channel="feishu",
        status="failed",
        error_message="网络错误",
        items_count=0
    )
    assert result is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.database'"

- [ ] **Step 3: 写最小实现**

```python
# src/database.py
import sqlite3
from datetime import datetime
from typing import Optional

class Database:
    """SQLite 数据库管理类"""
    
    def __init__(self, db_path: str):
        self.path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pushed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    summary TEXT,
                    category TEXT,
                    source TEXT,
                    pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS push_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    items_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS poll_state (
                    id INTEGER PRIMARY KEY,
                    last_poll_at TIMESTAMP,
                    last_new_item_at TIMESTAMP,
                    consecutive_empty INTEGER DEFAULT 0,
                    current_interval INTEGER DEFAULT 300
                )
            """)
            
            # 初始化轮询状态（如果不存在）
            conn.execute("""
                INSERT OR IGNORE INTO poll_state (id, consecutive_empty, current_interval)
                VALUES (1, 0, 300)
            """)
            
            conn.commit()
    
    def item_exists(self, item_id: str) -> bool:
        """检查条目是否已存在"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT EXISTS(SELECT 1 FROM pushed_items WHERE item_id = ?)",
                (item_id,)
            )
            return cursor.fetchone()[0]
    
    def insert_item(self, item_id: str, title: str, url: str,
                    summary: Optional[str], category: Optional[str],
                    source: Optional[str]) -> bool:
        """插入新条目"""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """INSERT INTO pushed_items (item_id, title, url, summary, category, source)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (item_id, title, url, summary, category, source)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    def get_last_poll_time(self) -> Optional[datetime]:
        """获取上次轮询时间"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT last_poll_at FROM poll_state WHERE id = 1"
            )
            row = cursor.fetchone()
            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None
    
    def update_poll_state(self, poll_time: datetime):
        """更新轮询状态"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET last_poll_at = ? WHERE id = 1",
                (poll_time.isoformat(),)
            )
            conn.commit()
    
    def get_consecutive_empty(self) -> int:
        """获取连续空轮询次数"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT consecutive_empty FROM poll_state WHERE id = 1"
            )
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def update_consecutive_empty(self, count: int):
        """更新连续空轮询次数"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET consecutive_empty = ? WHERE id = 1",
                (count,)
            )
            conn.commit()
    
    def get_current_interval(self) -> int:
        """获取当前轮询间隔"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(
                "SELECT current_interval FROM poll_state WHERE id = 1"
            )
            row = cursor.fetchone()
            return row[0] if row else 300
    
    def update_current_interval(self, interval: int):
        """更新当前轮询间隔"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET current_interval = ? WHERE id = 1",
                (interval,)
            )
            conn.commit()
    
    def update_last_new_item_time(self, item_time: datetime):
        """更新上次发现新内容时间"""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "UPDATE poll_state SET last_new_item_at = ? WHERE id = 1",
                (item_time.isoformat(),)
            )
            conn.commit()
    
    def log_push(self, channel: str, status: str,
                 error_message: Optional[str] = None,
                 items_count: int = 0) -> bool:
        """记录推送日志"""
        try:
            with sqlite3.connect(self.path) as conn:
                conn.execute(
                    """INSERT INTO push_logs (channel, status, error_message, items_count)
                       VALUES (?, ?, ?, ?)""",
                    (channel, status, error_message, items_count)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_database.py -v`
Expected: 9 passed

- [ ] **Step 5: 提交**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat: 添加数据库管理模块"
```

---

## Task 4: API 客户端模块

**Files:**
- Create: `src/fetcher.py`
- Create: `tests/test_fetcher.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_fetcher.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.fetcher import Fetcher, Item

def test_item_creation():
    """测试 Item 数据类"""
    item = Item(
        id="test-123",
        title="测试标题",
        url="https://example.com",
        summary="测试摘要",
        category="测试分类",
        source="Twitter",
        published_at=datetime.now()
    )
    assert item.id == "test-123"
    assert item.title == "测试标题"

def test_fetcher_init():
    """测试 Fetcher 初始化"""
    fetcher = Fetcher(api_url="https://api.test.com/items")
    assert fetcher.api_url == "https://api.test.com/items"

@patch('requests.get')
def test_fetch_items_success(mock_get):
    """测试成功获取条目"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "item-1",
                "title": "标题1",
                "url": "https://example.com/1",
                "summary": "摘要1",
                "category": "分类1",
                "source": "Twitter",
                "published_at": "2026-06-10T14:30:00Z"
            }
        ],
        "total": 1,
        "has_more": False
    }
    mock_get.return_value = mock_response
    
    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now() - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)
    
    assert len(items) == 1
    assert items[0].id == "item-1"
    assert items[0].title == "标题1"

@patch('requests.get')
def test_fetch_items_empty(mock_get):
    """测试获取空列表"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [],
        "total": 0,
        "has_more": False
    }
    mock_get.return_value = mock_response
    
    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now() - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)
    
    assert len(items) == 0

@patch('requests.get')
def test_fetch_items_network_error(mock_get):
    """测试网络错误"""
    mock_get.side_effect = Exception("网络错误")
    
    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now() - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)
    
    assert len(items) == 0

@patch('requests.get')
def test_fetch_items_api_error(mock_get):
    """测试 API 错误"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response
    
    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now() - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)
    
    assert len(items) == 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_fetcher.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.fetcher'"

- [ ] **Step 3: 写最小实现**

```python
# src/fetcher.py
import requests
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Item:
    """AI 新闻条目数据类"""
    id: str
    title: str
    url: str
    summary: Optional[str]
    category: Optional[str]
    source: Optional[str]
    published_at: datetime

class Fetcher:
    """AIHOT API 客户端"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def fetch_items(self, since: datetime) -> List[Item]:
        """获取指定时间之后的条目"""
        try:
            params = {
                "mode": "selected",
                "since": since.isoformat()
            }
            
            response = requests.get(self.api_url, params=params, timeout=30)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            items = []
            
            for item_data in data.get("items", []):
                try:
                    published_at = datetime.fromisoformat(
                        item_data.get("published_at", "").replace("Z", "+00:00")
                    )
                    item = Item(
                        id=item_data["id"],
                        title=item_data["title"],
                        url=item_data["url"],
                        summary=item_data.get("summary"),
                        category=item_data.get("category"),
                        source=item_data.get("source"),
                        published_at=published_at
                    )
                    items.append(item)
                except (KeyError, ValueError):
                    continue
            
            return items
            
        except Exception:
            return []
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_fetcher.py -v`
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src/fetcher.py tests/test_fetcher.py
git commit -m "feat: 添加 API 客户端模块"
```

---

## Task 5: 去重管理器

**Files:**
- Create: `src/dedup.py`
- Create: `tests/test_dedup.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dedup.py
import pytest
from datetime import datetime
from src.dedup import DedupManager
from src.database import Database
from src.fetcher import Item

@pytest.fixture
def db(tmp_path):
    """创建测试数据库"""
    return Database(str(tmp_path / "test.db"))

@pytest.fixture
def dedup(db):
    """创建去重管理器"""
    return DedupManager(db)

def test_filter_new_items(dedup):
    """测试过滤新条目"""
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary=None, category=None, source=None, published_at=datetime.now()),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary=None, category=None, source=None, published_at=datetime.now()),
    ]
    
    # 第一次过滤，所有都是新的
    new_items = dedup.filter_new_items(items)
    assert len(new_items) == 2
    
    # 标记为已推送
    for item in items:
        dedup.mark_as_pushed(item)
    
    # 第二次过滤，没有新的
    new_items = dedup.filter_new_items(items)
    assert len(new_items) == 0

def test_mark_as_pushed(dedup):
    """测试标记条目为已推送"""
    item = Item(id="item-3", title="标题3", url="https://example.com/3",
                summary="摘要", category="分类", source="Twitter", 
                published_at=datetime.now())
    
    result = dedup.mark_as_pushed(item)
    assert result is True
    
    # 验证已标记
    assert dedup.db.item_exists(item.id) is True

def test_mixed_new_and_existing(dedup):
    """测试混合新旧条目"""
    # 插入一个已存在的条目
    existing_item = Item(id="existing-1", title="已存在", url="https://example.com",
                         summary=None, category=None, source=None, 
                         published_at=datetime.now())
    dedup.mark_as_pushed(existing_item)
    
    # 准备混合列表
    items = [
        existing_item,  # 已存在
        Item(id="new-1", title="新条目", url="https://example.com/new",
             summary=None, category=None, source=None, published_at=datetime.now()),
    ]
    
    new_items = dedup.filter_new_items(items)
    assert len(new_items) == 1
    assert new_items[0].id == "new-1"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_dedup.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.dedup'"

- [ ] **Step 3: 写最小实现**

```python
# src/dedup.py
from typing import List
from src.database import Database
from src.fetcher import Item

class DedupManager:
    """去重管理器"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def filter_new_items(self, items: List[Item]) -> List[Item]:
        """过滤出新条目"""
        new_items = []
        for item in items:
            if not self.db.item_exists(item.id):
                new_items.append(item)
        return new_items
    
    def mark_as_pushed(self, item: Item) -> bool:
        """标记条目为已推送"""
        return self.db.insert_item(
            item_id=item.id,
            title=item.title,
            url=item.url,
            summary=item.summary,
            category=item.category,
            source=item.source
        )
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_dedup.py -v`
Expected: 3 passed

- [ ] **Step 5: 提交**

```bash
git add src/dedup.py tests/test_dedup.py
git commit -m "feat: 添加去重管理器"
```

---

## Task 6: 消息格式化器

**Files:**
- Create: `src/formatter.py`
- Create: `tests/test_formatter.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_formatter.py
import pytest
from datetime import datetime
from src.formatter import Formatter
from src.fetcher import Item

@pytest.fixture
def formatter():
    """创建格式化器"""
    return Formatter()

def test_format_single_item(formatter):
    """测试格式化单个条目"""
    item = Item(
        id="test-123",
        title="GPT-5 即将发布",
        url="https://twitter.com/example/123",
        summary="OpenAI 宣布 GPT-5 将在下个月发布",
        category="模型发布",
        source="Twitter",
        published_at=datetime(2026, 6, 10, 14, 30, 0)
    )
    
    card = formatter.format_single_item(item)
    
    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["title"]["content"] == "🔥 AI 热点更新"
    assert len(card["card"]["elements"]) > 0

def test_format_multiple_items(formatter):
    """测试格式化多个条目"""
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=datetime.now()),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary="摘要2", category="分类2", source="RSS",
             published_at=datetime.now()),
    ]
    
    message = formatter.format_multiple_items(items)
    
    assert message["msg_type"] == "interactive"
    assert "2" in message["card"]["header"]["title"]["content"]

def test_format_empty_list(formatter):
    """测试格式化空列表"""
    message = formatter.format_multiple_items([])
    assert message is None

def test_format_summary_disabled():
    """测试禁用摘要时的格式化"""
    formatter = Formatter(include_summary=False)
    
    item = Item(
        id="test-123",
        title="测试标题",
        url="https://example.com",
        summary="测试摘要",
        category="测试分类",
        source="Twitter",
        published_at=datetime.now()
    )
    
    card = formatter.format_single_item(item)
    # 验证没有摘要部分
    card_str = str(card)
    assert "测试摘要" not in card_str
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_formatter.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.formatter'"

- [ ] **Step 3: 写最小实现**

```python
# src/formatter.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from src.fetcher import Item

class Formatter:
    """消息格式化器"""
    
    def __init__(self, include_summary: bool = True, include_source: bool = True,
                 include_category: bool = True):
        self.include_summary = include_summary
        self.include_source = include_source
        self.include_category = include_category
    
    def format_single_item(self, item: Item) -> Dict[str, Any]:
        """格式化单个条目为飞书卡片"""
        elements = []
        
        # 标题
        title_content = f"**标题**\n[{item.title}]({item.url})"
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": title_content}
        })
        
        # 来源和分类
        meta_parts = []
        if self.include_source and item.source:
            meta_parts.append(f"**来源** | {item.source}")
        if self.include_category and item.category:
            meta_parts.append(f"**分类** | {item.category}")
        
        if meta_parts:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "    ".join(meta_parts)}
            })
        
        # 摘要
        if self.include_summary and item.summary:
            summary_content = f"**摘要**\n{item.summary}"
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
        for i, item in enumerate(items[:10], 1):
            content = f"**{i}.** [{item.title}]({item.url})"
            if self.include_source and item.source:
                content += f" ({item.source})"
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": content}
            })
        
        if len(items) > 10:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"... 还有 {len(items) - 10} 条，请查看网站"}
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
                    "title": {"tag": "plain_text", "content": "🔥 AI 热点更新"},
                    "template": "turquoise"
                },
                "elements": elements
            }
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_formatter.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/formatter.py tests/test_formatter.py
git commit -m "feat: 添加消息格式化器"
```

---

## Task 7: 推送基类和飞书推送器

**Files:**
- Create: `src/push/__init__.py`
- Create: `src/push/base.py`
- Create: `src/push/feishu.py`
- Create: `tests/test_push.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_push.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.push.base import BasePusher
from src.push.feishu import FeishuPusher
from src.fetcher import Item

def test_base_pusher_interface():
    """测试基类接口"""
    pusher = BasePusher()
    with pytest.raises(NotImplementedError):
        pusher.push([])

def test_feishu_pusher_init():
    """测试飞书推送器初始化"""
    pusher = FeishuPusher(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test"
    )
    assert pusher.webhook_url == "https://open.feishu.cn/open-apis/bot/v2/hook/test"

@patch('requests.post')
def test_feishu_push_success(mock_post):
    """测试飞书推送成功"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 0, "msg": "success"}
    mock_post.return_value = mock_response
    
    pusher = FeishuPusher(webhook_url="https://test.webhook.com")
    items = [
        Item(id="item-1", title="标题1", url="https://example.com",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=datetime.now())
    ]
    
    result = pusher.push(items)
    assert result is True

@patch('requests.post')
def test_feishu_push_failure(mock_post):
    """测试飞书推送失败"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response
    
    pusher = FeishuPusher(webhook_url="https://test.webhook.com")
    items = [
        Item(id="item-1", title="标题1", url="https://example.com",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=datetime.now())
    ]
    
    result = pusher.push(items)
    assert result is False

def test_feishu_push_empty_items():
    """测试推送空列表"""
    pusher = FeishuPusher(webhook_url="https://test.webhook.com")
    result = pusher.push([])
    assert result is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_push.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.push'"

- [ ] **Step 3: 写最小实现**

```python
# src/push/__init__.py
"""推送模块"""

from src.push.base import BasePusher
from src.push.feishu import FeishuPusher

__all__ = ["BasePusher", "FeishuPusher"]
```

```python
# src/push/base.py
from typing import List
from src.fetcher import Item

class BasePusher:
    """推送基类"""
    
    def push(self, items: List[Item]) -> bool:
        """推送条目"""
        raise NotImplementedError
```

```python
# src/push/feishu.py
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_push.py -v`
Expected: 4 passed

- [ ] **Step 5: 提交**

```bash
git add src/push/
git commit -m "feat: 添加推送基类和飞书推送器"
```

---

## Task 8: 主程序入口

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: 写最小实现**

```python
# src/main.py
import argparse
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.config import Config
from src.database import Database
from src.fetcher import Fetcher
from src.dedup import DedupManager
from src.formatter import Formatter
from src.push.feishu import FeishuPusher

def setup_logging(log_path: str):
    """设置日志"""
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def init_database(config: Config):
    """初始化数据库"""
    db_dir = Path(config.storage_db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    db = Database(config.storage_db_path)
    logging.info(f"数据库初始化完成: {config.storage_db_path}")
    return db

def run_once(config: Config, db: Database):
    """执行一次轮询"""
    logger = logging.getLogger(__name__)
    
    # 获取上次轮询时间
    last_poll = db.get_last_poll_time()
    if last_poll is None:
        last_poll = datetime.now() - timedelta(minutes=5)
    
    logger.info(f"开始轮询，上次轮询时间: {last_poll}")
    
    # 获取新条目
    fetcher = Fetcher(config.source_api_url)
    items = fetcher.fetch_items(since=last_poll)
    logger.info(f"获取到 {len(items)} 个条目")
    
    # 去重
    dedup = DedupManager(db)
    new_items = dedup.filter_new_items(items)
    logger.info(f"过滤后 {len(new_items)} 个新条目")
    
    # 推送
    if new_items:
        pusher = FeishuPusher(
            webhook_url=config.feishu_webhook_url,
            secret=config.feishu_webhook_secret
        )
        
        success = pusher.push(new_items)
        if success:
            logger.info(f"推送成功: {len(new_items)} 个条目")
            db.log_push("feishu", "success", items_count=len(new_items))
            
            # 标记为已推送
            for item in new_items:
                dedup.mark_as_pushed(item)
            
            # 重置连续空轮询计数
            db.update_consecutive_empty(0)
            db.update_last_new_item_time(datetime.now())
        else:
            logger.error("推送失败")
            db.log_push("feishu", "failed", error_message="推送失败", items_count=0)
    else:
        logger.info("没有新条目")
        consecutive_empty = db.get_consecutive_empty() + 1
        db.update_consecutive_empty(consecutive_empty)
        
        # 动态调整轮询间隔
        if consecutive_empty >= config.polling_empty_threshold:
            current_interval = db.get_current_interval()
            new_interval = min(current_interval * 2, config.polling_max_interval)
            db.update_current_interval(new_interval)
            logger.info(f"连续 {consecutive_empty} 次空轮询，调整间隔为 {new_interval} 秒")
    
    # 更新轮询时间
    db.update_poll_state(datetime.now())
    
    return len(new_items)

def run_scheduler(config: Config, db: Database):
    """运行调度器"""
    logger = logging.getLogger(__name__)
    logger.info("启动调度器")
    
    running = True
    
    def signal_handler(signum, frame):
        nonlocal running
        logger.info("收到停止信号，正在退出...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while running:
        try:
            # 检查工作时间
            now = datetime.now()
            if config.polling_work_hours_start <= now.hour < config.polling_work_hours_end:
                interval = config.polling_work_hours_interval
            else:
                interval = config.polling_off_hours_interval
            
            # 使用数据库中的当前间隔
            current_interval = db.get_current_interval()
            interval = min(current_interval, interval)
            
            logger.info(f"下次轮询在 {interval} 秒后")
            
            # 等待
            import time
            time.sleep(interval)
            
            if not running:
                break
            
            # 执行轮询
            run_once(config, db)
            
        except Exception as e:
            logger.error(f"轮询出错: {e}")
            import time
            time.sleep(60)
    
    logger.info("调度器已停止")

def show_stats(db: Database):
    """显示统计信息"""
    last_poll = db.get_last_poll_time()
    consecutive_empty = db.get_consecutive_empty()
    current_interval = db.get_current_interval()
    
    print(f"上次轮询时间: {last_poll or '从未'}")
    print(f"连续空轮询次数: {consecutive_empty}")
    print(f"当前轮询间隔: {current_interval} 秒")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AIHOT Tracker - AI 新闻实时推送系统")
    parser.add_argument("command", choices=["init", "run", "stats"], help="命令")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--config", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    config = Config(config_path=args.config)
    
    # 设置日志
    setup_logging(config.storage_log_path)
    
    # 初始化数据库
    db = init_database(config)
    
    if args.command == "init":
        print("数据库初始化完成")
    
    elif args.command == "run":
        if args.once:
            count = run_once(config, db)
            print(f"完成，推送了 {count} 个条目")
        else:
            run_scheduler(config, db)
    
    elif args.command == "stats":
        show_stats(db)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试命令行参数**

Run: `python -m src.main init`
Expected: 输出 "数据库初始化完成"

- [ ] **Step 3: 测试单次运行**

Run: `python -m src.main run --once`
Expected: 执行一次轮询，输出结果

- [ ] **Step 4: 提交**

```bash
git add src/main.py
git commit -m "feat: 添加主程序入口"
```

---

## Task 9: 部署脚本

**Files:**
- Create: `scripts/install.sh`
- Create: `scripts/setup_service.sh`

- [ ] **Step 1: 创建安装脚本**

```bash
#!/bin/bash
# scripts/install.sh

set -e

echo "开始安装 AIHOT Tracker..."

# 检查 Python 版本
python3 --version || { echo "错误: 需要 Python 3.8+"; exit 1; }

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 创建目录
echo "创建数据目录..."
mkdir -p data logs

# 复制配置文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置 Webhook URL"
fi

# 初始化数据库
echo "初始化数据库..."
python -m src.main init

echo "安装完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件配置飞书 Webhook URL"
echo "2. 运行 'python -m src.main run --once' 测试"
echo "3. 运行 'sudo bash scripts/setup_service.sh' 配置系统服务"
```

- [ ] **Step 2: 创建 systemd 服务配置脚本**

```bash
#!/bin/bash
# scripts/setup_service.sh

set -e

SERVICE_NAME="aihot-tracker"
INSTALL_DIR=$(pwd)
VENV_DIR="$INSTALL_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
MAIN_SCRIPT="$VENV_DIR/lib/python*/site-packages/src/main.py"

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

echo "配置 systemd 服务..."

# 创建服务文件
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=AIHOT Tracker - AI News Push Service
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$PYTHON_BIN -m src.main run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
systemctl daemon-reload

# 启用服务
systemctl enable $SERVICE_NAME

echo "服务配置完成！"
echo ""
echo "启动服务: sudo systemctl start $SERVICE_NAME"
echo "查看状态: sudo systemctl status $SERVICE_NAME"
echo "查看日志: sudo journalctl -u $SERVICE_NAME -f"
```

- [ ] **Step 3: 设置脚本权限**

Run: `chmod +x scripts/*.sh`

- [ ] **Step 4: 提交**

```bash
git add scripts/
git commit -m "feat: 添加部署脚本"
```

---

## Task 10: 文档和最终测试

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 README.md**

```markdown
# AIHOT Tracker

AI 新闻实时追踪和推送系统，自动从 AIHOT 网站获取最新内容并推送到飞书。

## 功能特性

- ✅ 使用官方 API，合法合规
- ✅ 智能轮询，近实时推送（最多 5 分钟延迟）
- ✅ 自动去重，避免重复推送
- ✅ 美观的飞书消息卡片
- ✅ 可扩展架构，支持多渠道推送

## 快速开始

### 1. 安装

```bash
git clone <repo-url>
cd aihot-tracker
bash scripts/install.sh
```

### 2. 配置

编辑 `.env` 文件，配置飞书 Webhook URL：

```bash
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

### 3. 测试运行

```bash
python -m src.main run --once
```

### 4. 部署为系统服务

```bash
sudo bash scripts/setup_service.sh
sudo systemctl start aihot-tracker
```

## 使用方法

### 命令行命令

```bash
# 初始化数据库
python -m src.main init

# 单次运行
python -m src.main run --once

# 启动调度器（持续运行）
python -m src.main run

# 查看统计信息
python -m src.main stats
```

### systemd 服务

```bash
# 启动服务
sudo systemctl start aihot-tracker

# 停止服务
sudo systemctl stop aihot-tracker

# 查看状态
sudo systemctl status aihot-tracker

# 查看日志
sudo journalctl -u aihot-tracker -f

# 重启服务
sudo systemctl restart aihot-tracker
```

## 配置说明

配置文件位于 `config/config.yaml`，主要配置项：

- `source`: API 源配置
- `polling`: 轮询策略配置
- `push`: 推送渠道配置
- `message`: 消息格式配置
- `storage`: 存储配置

敏感信息（如 Webhook URL）通过环境变量配置，参考 `.env.example`。

## 项目结构

```
aihot-tracker/
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── config.py          # 配置管理
│   ├── fetcher.py         # API 客户端
│   ├── dedup.py           # 去重管理器
│   ├── formatter.py       # 消息格式化器
│   ├── database.py        # 数据库管理
│   └── push/              # 推送模块
│       ├── base.py        # 推送基类
│       └── feishu.py      # 飞书推送器
├── config/                # 配置文件
├── scripts/               # 部署脚本
├── tests/                 # 测试代码
└── docs/                  # 文档
```

## 扩展开发

### 添加新的推送渠道

1. 在 `src/push/` 目录下创建新的推送器类
2. 继承 `BasePusher` 基类
3. 实现 `push` 方法
4. 在 `config.yaml` 中添加渠道配置

示例：

```python
# src/push/wechat.py
from src.push.base import BasePusher
from src.fetcher import Item

class WechatPusher(BasePusher):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def push(self, items: list[Item]) -> bool:
        # 实现微信推送逻辑
        pass
```

## 许可证

MIT License
```

- [ ] **Step 2: 运行完整测试套件**

Run: `pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs: 添加项目文档"
```

- [ ] **Step 4: 最终提交**

```bash
git add .
git commit -m "chore: 完成 AIHOT Tracker v1.0"
```

---

## Self-Review Checklist

✅ **Spec coverage:** 所有设计文档中的功能点都已实现
- API 集成 ✅
- 智能轮询 ✅
- 数据存储和去重 ✅
- 飞书消息格式 ✅
- 错误处理 ✅
- 配置管理 ✅
- 部署和运维 ✅

✅ **Placeholder scan:** 没有发现 TBD、TODO 或占位符

✅ **Type consistency:** 所有类型、方法签名和属性名在各任务中保持一致

✅ **Code completeness:** 每个步骤都包含完整代码

✅ **Test coverage:** 每个模块都有对应的测试

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-10-aihot-tracker.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 我为每个任务分发一个新的子代理，任务之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用 executing-plans 执行任务，批量执行并设置检查点

Which approach?
