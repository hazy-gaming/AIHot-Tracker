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
