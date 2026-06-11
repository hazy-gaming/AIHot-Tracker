import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from src.push.base import BasePusher
from src.push.feishu import FeishuPusher
from src.fetcher import Item

def test_base_pusher_interface():
    """测试基类接口 - 无法直接实例化抽象类"""
    with pytest.raises(TypeError):
        BasePusher()

    # 未实现 push 方法的子类也无法实例化
    class IncompletePusher(BasePusher):
        pass

    with pytest.raises(TypeError):
        IncompletePusher()

    # 实现了 push 方法的子类可以实例化
    class CompletePusher(BasePusher):
        def push(self, items):
            return True

    pusher = CompletePusher()
    assert pusher.push([]) is True

def test_feishu_pusher_init():
    """测试飞书推送器初始化"""
    pusher = FeishuPusher(
        webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/test",
        include_summary=False,
        max_items=3
    )
    assert pusher.webhook_url == "https://open.feishu.cn/open-apis/bot/v2/hook/test"
    assert pusher.formatter.include_summary is False
    assert pusher.formatter.max_items == 3

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
             published_at=datetime.now(timezone.utc))
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
             published_at=datetime.now(timezone.utc))
    ]

    result = pusher.push(items)
    assert result is False

def test_feishu_push_empty_items():
    """测试推送空列表"""
    pusher = FeishuPusher(webhook_url="https://test.webhook.com")
    result = pusher.push([])
    assert result is True

@patch('requests.post')
def test_feishu_push_sign_with_formatter_config(mock_post):
    """测试签名逻辑不受格式化配置影响"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"code": 0, "msg": "success"}
    mock_post.return_value = mock_response

    pusher = FeishuPusher(
        webhook_url="https://test.webhook.com",
        secret="test-secret",
        include_summary=False,
        max_items=1
    )
    items = [
        Item(id="item-1", title="标题1", url="https://example.com/1",
             summary="摘要1", category="分类1", source="Twitter",
             published_at=datetime.now(timezone.utc)),
        Item(id="item-2", title="标题2", url="https://example.com/2",
             summary="摘要2", category="分类2", source="RSS",
             published_at=datetime.now(timezone.utc)),
    ]

    result = pusher.push(items)

    assert result is True
    payload = mock_post.call_args.kwargs["json"]
    assert payload["timestamp"]
    assert payload["sign"]
    assert "摘要1" not in str(payload)
    assert "还有 1 条" in str(payload)
