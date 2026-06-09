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
