import pytest
from src.config import Config

@pytest.fixture
def default_config(tmp_path):
    """创建默认测试配置"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
source:
  api_url: "https://aihot.virxact.com/api/public/items"
polling:
  base_interval: 300
  min_interval: 60
  max_interval: 900
""")
    return Config(config_path=str(config_file))

def test_config_load_default(default_config):
    """测试默认配置加载"""
    assert default_config.source_api_url == "https://aihot.virxact.com/api/public/items"
    assert default_config.polling_base_interval == 300

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

def test_config_polling_interval(default_config):
    """测试轮询间隔配置"""
    assert default_config.polling_base_interval == 300
    assert default_config.polling_min_interval == 60
    assert default_config.polling_max_interval == 900