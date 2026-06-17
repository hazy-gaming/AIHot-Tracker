import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from src.push.feishu_bitable import FeishuBitableWriter
from src.fetcher import Item


def _make_item(**overrides):
    defaults = dict(
        id="item-1", title="测试标题", url="https://example.com",
        summary="测试摘要", category="AI", source="Twitter",
        published_at=datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return Item(**defaults)


class TestTokenAcquisition:
    """测试 token 获取"""

    @patch('requests.post')
    def test_get_token_success(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 0, "tenant_access_token": "t-abc", "expire": 7200}
        mock_post.return_value = mock_resp

        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        token = writer._get_tenant_access_token()

        assert token == "t-abc"
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_get_token_caches(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 0, "tenant_access_token": "t-abc", "expire": 7200}
        mock_post.return_value = mock_resp

        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        writer._get_tenant_access_token()
        writer._get_tenant_access_token()

        assert mock_post.call_count == 1

    @patch('requests.post')
    def test_get_token_failure(self, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 10003, "msg": "invalid app_id"}
        mock_post.return_value = mock_resp

        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        token = writer._get_tenant_access_token()

        assert token is None


class TestItemToFields:
    """测试 Item → 多维表格字段转换"""

    def test_default_mapping(self):
        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        item = _make_item()
        fields = writer._item_to_fields(item)

        assert fields["标题"] == "测试标题"
        assert fields["链接"] == "https://example.com"
        assert fields["摘要"] == "测试摘要"
        assert fields["分类"] == "AI"
        assert fields["来源"] == "Twitter"
        assert fields["发布时间"] == "2026-06-10 12:00:00"

    def test_custom_mapping(self):
        writer = FeishuBitableWriter(
            "id", "secret", "app_t", "tbl_t",
            field_mapping={"title": "Name", "url": "Link"}
        )
        item = _make_item()
        fields = writer._item_to_fields(item)

        assert fields == {"Name": "测试标题", "Link": "https://example.com"}

    def test_none_fields_skipped(self):
        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        item = _make_item(summary=None, category=None)
        fields = writer._item_to_fields(item)

        assert "摘要" not in fields
        assert "分类" not in fields


class TestWrite:
    """测试写入多维表格"""

    @patch('requests.post')
    def test_write_empty_list(self, mock_post):
        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        result = writer.write([])

        assert result is True
        mock_post.assert_not_called()

    @patch.object(FeishuBitableWriter, '_get_tenant_access_token', return_value=None)
    def test_write_no_token(self, mock_token):
        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        result = writer.write([_make_item()])

        assert result is False

    @patch('requests.post')
    @patch.object(FeishuBitableWriter, '_get_tenant_access_token', return_value="t-test")
    def test_write_success(self, mock_token, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_resp

        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        items = [_make_item(id="1"), _make_item(id="2", title="标题2")]
        result = writer.write(items)

        assert result is True
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["headers"]["Authorization"] == "Bearer t-test"
        records = call_kwargs[1]["json"]["records"]
        assert len(records) == 2

    @patch('requests.post')
    @patch.object(FeishuBitableWriter, '_get_tenant_access_token', return_value="t-test")
    def test_write_api_error(self, mock_token, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 1254043, "msg": "table not found"}
        mock_post.return_value = mock_resp

        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        result = writer.write([_make_item()])

        assert result is False

    @patch('requests.post')
    @patch.object(FeishuBitableWriter, '_get_tenant_access_token', return_value="t-test")
    def test_write_http_error(self, mock_token, mock_post):
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_post.return_value = mock_resp

        writer = FeishuBitableWriter("id", "secret", "app_t", "tbl_t")
        result = writer.write([_make_item()])

        assert result is False
