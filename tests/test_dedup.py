import pytest
from datetime import datetime, timezone
from src.dedup import DedupManager
from src.database import Database
from src.fetcher import Item

@pytest.fixture
def db(tmp_path):
    """创建测试数据库"""
    database = Database(str(tmp_path / "test.db"))
    yield database
    database.close()

@pytest.fixture
def dedup(db):
    """创建去重管理器"""
    return DedupManager(db)

def test_filter_new_items(dedup):
    """测试过滤新条目"""
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary=None, category=None, source=None, published_at=datetime.now(timezone.utc)),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary=None, category=None, source=None, published_at=datetime.now(timezone.utc)),
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
                published_at=datetime.now(timezone.utc))

    result = dedup.mark_as_pushed(item)
    assert result is True

    # 验证已标记
    assert dedup.db.item_exists(item.id) is True

def test_mixed_new_and_existing(dedup):
    """测试混合新旧条目"""
    # 插入一个已存在的条目
    existing_item = Item(id="existing-1", title="已存在", url="https://example.com",
                         summary=None, category=None, source=None,
                         published_at=datetime.now(timezone.utc))
    dedup.mark_as_pushed(existing_item)

    # 准备混合列表
    items = [
        existing_item,  # 已存在
        Item(id="new-1", title="新条目", url="https://example.com/new",
             summary=None, category=None, source=None, published_at=datetime.now(timezone.utc)),
    ]

    new_items = dedup.filter_new_items(items)
    assert len(new_items) == 1
    assert new_items[0].id == "new-1"
