import pytest
from datetime import datetime, timezone
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
    published_at = datetime(2026, 6, 10, 14, 30, 0, tzinfo=timezone.utc)
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=published_at),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary="摘要2", category="分类2", source="RSS",
             published_at=published_at),
    ]

    message = formatter.format_multiple_items(items)

    assert message["msg_type"] == "interactive"
    assert "2" in message["card"]["header"]["title"]["content"]
    card_str = str(message)
    assert "摘要1" in card_str
    assert "摘要2" in card_str
    assert "分类1" in card_str
    assert "Twitter" in card_str
    assert "2026-06-10 14:30" in card_str

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
        published_at=datetime.now(timezone.utc)
    )

    card = formatter.format_single_item(item)
    # 验证没有摘要部分
    card_str = str(card)
    assert "测试摘要" not in card_str

def test_format_multiple_items_summary_disabled():
    """测试多条消息禁用摘要时不包含摘要"""
    formatter = Formatter(include_summary=False)
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=datetime.now(timezone.utc)),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary="摘要2", category="分类2", source="RSS",
             published_at=datetime.now(timezone.utc)),
    ]

    message = formatter.format_multiple_items(items)

    assert "摘要1" not in str(message)
    assert "摘要2" not in str(message)

def test_format_multiple_items_respects_max_items():
    """测试多条消息遵守最大条目数"""
    formatter = Formatter(max_items=1)
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=datetime.now(timezone.utc)),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary="摘要2", category="分类2", source="RSS",
             published_at=datetime.now(timezone.utc)),
    ]

    message = formatter.format_multiple_items(items)
    card_str = str(message)

    assert "标题1" in card_str
    assert "标题2" not in card_str
    assert "还有 1 条" in card_str
