import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, call
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
    assert item.title_en is None
    assert item.score is None
    assert item.permalink is None


def test_item_creation_with_extended_fields():
    """测试 Item 数据类扩展字段"""
    item = Item(
        id="test-123",
        title="测试标题",
        url="https://example.com",
        summary=None,
        category=None,
        source=None,
        published_at=None,
        title_en="Test Title",
        score=85,
        permalink="https://aihot.virxact.com/items/test-123"
    )
    assert item.title_en == "Test Title"
    assert item.score == 85
    assert item.permalink == "https://aihot.virxact.com/items/test-123"
    assert item.published_at is None


def test_fetcher_init():
    """测试 Fetcher 初始化"""
    fetcher = Fetcher(api_url="https://api.test.com/items")
    assert fetcher.api_url == "https://api.test.com/items"
    assert fetcher.mode == "selected"
    assert fetcher.take == 100


def test_fetcher_init_take_clamped():
    """测试 take 参数被限制在 1-100"""
    fetcher = Fetcher(api_url="https://api.test.com/items", take=200)
    assert fetcher.take == 100

    fetcher = Fetcher(api_url="https://api.test.com/items", take=0)
    assert fetcher.take == 1


@patch('requests.get')
def test_fetch_items_success(mock_get):
    """测试成功获取条目"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {
        "count": 1,
        "hasNext": False,
        "nextCursor": None,
        "items": [
            {
                "id": "item-1",
                "title": "标题1",
                "url": "https://example.com/1",
                "summary": "摘要1",
                "category": "分类1",
                "source": "Twitter",
                "publishedAt": "2026-06-10T14:30:00Z",
                "selected": True,
                "score": 80,
                "permalink": "https://aihot.virxact.com/items/item-1"
            }
        ],
    }
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 1
    assert items[0].id == "item-1"
    assert items[0].title == "标题1"
    assert items[0].score == 80
    assert items[0].permalink == "https://aihot.virxact.com/items/item-1"

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["mode"] == "selected"
    assert kwargs["params"]["take"] == 100
    assert "Mozilla/5.0" in kwargs["headers"]["User-Agent"]
    assert kwargs["headers"]["Referer"] == "https://aihot.virxact.com/"
    assert "application/json" in kwargs["headers"]["Accept"]


@patch('requests.get')
def test_fetch_items_pagination(mock_get):
    """测试分页：自动翻页直到 hasNext=False"""
    page1 = Mock()
    page1.status_code = 200
    page1.headers = {}
    page1.json.return_value = {
        "count": 2,
        "hasNext": True,
        "nextCursor": "cursor-page2",
        "items": [
            {
                "id": "item-1",
                "title": "标题1",
                "url": "https://example.com/1",
                "publishedAt": "2026-06-10T14:30:00Z",
            },
            {
                "id": "item-2",
                "title": "标题2",
                "url": "https://example.com/2",
                "publishedAt": "2026-06-10T14:31:00Z",
            },
        ],
    }

    page2 = Mock()
    page2.status_code = 200
    page2.headers = {}
    page2.json.return_value = {
        "count": 1,
        "hasNext": False,
        "nextCursor": None,
        "items": [
            {
                "id": "item-3",
                "title": "标题3",
                "url": "https://example.com/3",
                "publishedAt": "2026-06-10T14:32:00Z",
            },
        ],
    }

    mock_get.side_effect = [page1, page2]

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 3
    assert [i.id for i in items] == ["item-1", "item-2", "item-3"]

    # 第二次请求应带上 cursor
    second_call_params = mock_get.call_args_list[1][1]["params"]
    assert second_call_params["cursor"] == "cursor-page2"


@patch('requests.get')
def test_fetch_items_etag_304(mock_get):
    """测试 ETag 304 缓存：无新内容时返回空列表"""
    # 第一次请求：返回数据 + ETag
    first = Mock()
    first.status_code = 200
    first.headers = {"ETag": 'W/"items-abc123"'}
    first.json.return_value = {
        "count": 1,
        "hasNext": False,
        "nextCursor": None,
        "items": [
            {
                "id": "item-1",
                "title": "标题1",
                "url": "https://example.com/1",
                "publishedAt": "2026-06-10T14:30:00Z",
            },
        ],
    }

    # 第二次请求：304 无新内容
    second = Mock()
    second.status_code = 304
    second.headers = {}

    mock_get.side_effect = [first, second]

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)

    items1 = fetcher.fetch_items(since=since)
    assert len(items1) == 1

    items2 = fetcher.fetch_items(since=since)
    assert len(items2) == 0

    # 第二次请求应带上 If-None-Match
    second_call_headers = mock_get.call_args_list[1][1]["headers"]
    assert second_call_headers["If-None-Match"] == 'W/"items-abc123"'


@patch('requests.get')
def test_fetch_items_etag_only_from_first_page(mock_get):
    """测试分页时只保存首页 ETag，不被后续页覆盖"""
    page1 = Mock()
    page1.status_code = 200
    page1.headers = {"ETag": 'W/"items-page1-etag"'}
    page1.json.return_value = {
        "count": 2,
        "hasNext": True,
        "nextCursor": "cursor-p2",
        "items": [
            {"id": "item-1", "title": "t1", "url": "https://x/1", "publishedAt": "2026-06-10T14:30:00Z"},
            {"id": "item-2", "title": "t2", "url": "https://x/2", "publishedAt": "2026-06-10T14:31:00Z"},
        ],
    }

    page2 = Mock()
    page2.status_code = 200
    page2.headers = {"ETag": 'W/"items-page2-etag"'}
    page2.json.return_value = {
        "count": 1,
        "hasNext": False,
        "nextCursor": None,
        "items": [
            {"id": "item-3", "title": "t3", "url": "https://x/3", "publishedAt": "2026-06-10T14:32:00Z"},
        ],
    }

    # 第三、四次：用首页 ETag 请求首页 → 304
    etag_match = Mock()
    etag_match.status_code = 304
    etag_match.headers = {}

    mock_get.side_effect = [page1, page2, etag_match]

    fetcher = Fetcher(api_url="https://api.test.com/items", take=2)
    since = datetime.now(timezone.utc) - timedelta(minutes=5)

    items1 = fetcher.fetch_items(since=since)
    assert len(items1) == 3

    # ETag 应该是首页的，不是第二页的
    assert fetcher._etag == 'W/"items-page1-etag"'

    # 再次请求应 304
    items2 = fetcher.fetch_items(since=since)
    assert len(items2) == 0

    # 304 请求应带首页 ETag
    third_call_headers = mock_get.call_args_list[2][1]["headers"]
    assert third_call_headers["If-None-Match"] == 'W/"items-page1-etag"'


@patch('requests.get')
def test_fetch_items_selected_mode_keeps_items_without_selected_flag(mock_get):
    """测试 selected 模式不因缺少 selected 字段误丢条目"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {
        "count": 1,
        "hasNext": False,
        "nextCursor": None,
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
    mock_response.headers = {}
    mock_response.json.return_value = {
        "count": 2,
        "hasNext": False,
        "nextCursor": None,
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
    mock_response.headers = {}
    mock_response.json.return_value = {
        "count": 0,
        "hasNext": False,
        "nextCursor": None,
        "items": [],
    }
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 0


@patch('requests.get')
def test_fetch_items_null_published_at(mock_get):
    """测试 publishedAt 为 null 时使用当前时间兜底，不丢条目"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {
        "count": 1,
        "hasNext": False,
        "nextCursor": None,
        "items": [
            {
                "id": "item-no-time",
                "title": "无时间条目",
                "url": "https://example.com/1",
                "publishedAt": None,
            }
        ]
    }
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    before = datetime.now(timezone.utc)
    items = fetcher.fetch_items(since=before - timedelta(minutes=5))
    after = datetime.now(timezone.utc)

    assert len(items) == 1
    assert items[0].id == "item-no-time"
    assert before <= items[0].published_at <= after


@patch('requests.get')
def test_fetch_items_400_error_with_detail(mock_get):
    """测试 400 错误解析响应体中的 error 字段"""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": "invalid take (must be integer 1-100)"
    }
    mock_response.text = '{"error": "invalid take (must be integer 1-100)"}'
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    items = fetcher.fetch_items(since=datetime.now(timezone.utc) - timedelta(minutes=5))

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
    mock_response.text = "Internal Server Error"
    mock_response.json.side_effect = ValueError("not json")
    mock_get.return_value = mock_response

    fetcher = Fetcher(api_url="https://api.test.com/items")
    since = datetime.now(timezone.utc) - timedelta(minutes=5)
    items = fetcher.fetch_items(since=since)

    assert len(items) == 0
