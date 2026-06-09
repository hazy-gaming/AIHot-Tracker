# AIHOT Tracker

AI 新闻实时追踪和推送系统，自动从 AIHOT 网站获取最新内容并推送到飞书。

## 功能特性

- ✅ 使用官方 API，合法合规
- ✅ 智能轮询，近实时推送（最多 1 分钟延迟）
- ✅ 自动去重，避免重复推送
- ✅ 美观的飞书消息卡片
- ✅ 可扩展架构，支持多渠道推送
- ✅ 支持 Docker 部署

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/hazy-gaming/AIHot-Tracker.git
cd AIHot-Tracker

# 2. 配置环境变量
cp .env.example .env
vim .env
# 添加: FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的token

# 3. 启动容器
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 方式二：传统部署

```bash
# 1. 安装
git clone <repo-url>
cd aihot-tracker
bash scripts/install.sh

# 2. 配置
vim .env
# 添加: FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的token

# 3. 测试运行
source venv/bin/activate
python -m src.main run --once

# 4. 部署为系统服务
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
