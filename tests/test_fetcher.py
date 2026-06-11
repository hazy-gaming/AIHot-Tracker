import pytest
from datetime import datetime, timedelta, timezone
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
        published_at=datetime.now(timezone.utc)
    )
    assert item.id == "test-123"
    assert item.title == "测试标题"

def test_fetcher_init():
    """测试 Fetcher 初始化"""
    fetcher = Fetcher(api_url="https://api.test.com/items")
    assert fetcher.api_url == "https://api.test.com/items"
    assert fetcher.mode == "selected"

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
                "published_at": "2026-06-10T14:30:00Z",
                "selected": True
            }
        ],
        "total": 1,
        "has_more": False
    }
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 1
    assert items[0].id == "item-1"
    assert items[0].title == "标题1"

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["mode"] == "selected"
    assert "Mozilla/5.0" in kwargs["headers"]["User-Agent"]
    assert kwargs["headers"]["Referer"] == "https://aihot.virxact.com/"
    assert "application/json" in kwargs["headers"]["Accept"]

@patch('requests.get')
def test_fetch_items_selected_mode_keeps_items_without_selected_flag(mock_get):
    """测试 selected 模式不因缺少 selected 字段误丢条目"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "item-1",
                "title": "精选标题",
                "url": "https://example.com/1",
                "summary": "精选摘要",
                "category": "ai-products",
                "source": "AIHOT",
                "publishedAt": "2026-06-10T14:30:00.000Z"
            }
        ]
    }
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items", mode="selected")
    items = fetcher.fetch_items(since=datetime.now(timezone.utc) - timedelta(minutes=5))

    assert len(items) == 1
    assert items[0].published_at == datetime(2026, 6, 10, 14, 30, 0, tzinfo=timezone.utc)

@patch('requests.get')
def test_fetch_items_all_mode_filters_unselected_items(mock_get):
    """测试 all 模式仍过滤非精选条目"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "id": "item-1",
                "title": "非精选",
                "url": "https://example.com/1",
                "publishedAt": "2026-06-10T14:30:00Z",
                "selected": False
            },
            {
                "id": "item-2",
                "title": "精选",
                "url": "https://example.com/2",
                "publishedAt": "2026-06-10T14:31:00Z",
                "selected": True
            }
        ]
    }
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items", mode="all")
    items = fetcher.fetch_items(since=datetime.now(timezone.utc) - timedelta(minutes=5))

    assert [item.id for item in items] == ["item-2"]

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
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 0

@patch('requests.get')
def test_fetch_items_network_error(mock_get):
    """测试网络错误"""
    mock_get.side_effect = Exception("网络错误")

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 0

@patch('requests.get')
def test_fetch_items_api_error(mock_get):
    """测试 API 错误"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 0
