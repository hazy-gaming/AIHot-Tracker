# AIHOT Tracker

AI 新闻实时追踪和推送系统，自动从 AIHOT 网站获取最新内容并推送到飞书。

## 功能特性

- ✅ 使用官方 REST API（OpenAPI 3.1），合法合规
- ✅ 自动分页，`take=100` + cursor 翻页，不漏数据
- ✅ ETag 缓存，304 无新内容时不重传，节省 99% 带宽
- ✅ 智能轮询，近实时推送（最多 1 分钟延迟）
- ✅ 自动去重，避免重复推送
- ✅ 美观的飞书消息卡片
- ✅ 飞书多维表格（Bitable）自动写入
- ✅ 采集扩展字段：`score`（重要性评分）、`title_en`、`permalink`
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

- `source`: API 源配置（端点、模式、分类）
- `polling`: 轮询策略配置（间隔、工作时间、动态退避）
- `push`: 推送渠道配置（飞书 Webhook）
- `message`: 消息格式配置（条目数上限、摘要/来源/分类开关）
- `storage`: 存储配置（数据库路径、日志路径）
- `bitable`: 飞书多维表格配置（app_id、app_secret、app_token、table_id、字段映射）

敏感信息通过环境变量配置，参考 `.env.example`：

```bash
FEISHU_WEBHOOK_URL       # 飞书机器人 Webhook 地址
FEISHU_WEBHOOK_SECRET    # 飞书签名密钥（可选）
BITABLE_APP_ID           # 飞书应用 App ID
BITABLE_APP_SECRET       # 飞书应用 App Secret
BITABLE_APP_TOKEN        # 多维表格 app_token
BITABLE_TABLE_ID         # 数据表 table_id
```

## 项目结构

```
AIHot-Tracker/
├── src/                        # 源代码
│   ├── main.py                # 主程序入口 & 调度器
│   ├── config.py              # 配置管理（YAML + 环境变量）
│   ├── fetcher.py             # API 客户端（分页 + ETag）
│   ├── rss_fetcher.py         # RSS 备用数据源
│   ├── dedup.py               # 去重管理器
│   ├── formatter.py           # 飞书消息卡片格式化
│   ├── database.py            # SQLite 数据库管理
│   └── push/                  # 推送模块
│       ├── base.py            # 推送基类（抽象）
│       ├── feishu.py          # 飞书 Webhook 推送
│       └── feishu_bitable.py  # 飞书多维表格写入
├── config/                    # 配置文件
│   └── config.yaml
├── scripts/                   # 部署脚本
├── tests/                     # 测试代码
├── openapi.yaml               # AIHOT 官方 OpenAPI 3.1 规范
└── docs/                      # 文档
```

## API 对接说明

本项目对接 [AIHOT 官方 REST API](https://aihot.virxact.com/agent)，完整 OpenAPI 规范见 `openapi.yaml`。

### 数据字段

从 API 获取的每条新闻包含以下字段：

| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `id` | string | ✅ | 条目唯一 ID（cuid 25 字符） |
| `title` | string | ✅ | 中文标题 |
| `url` | string | ✅ | 原文链接 |
| `source` | string | 可空 | 来源名称（如 "Anthropic Blog"） |
| `summary` | string | 可空 | 中文摘要 |
| `category` | string | 可空 | 分类：`ai-models` / `ai-products` / `industry` / `paper` / `tip` |
| `published_at` | datetime | 可空 | 发布时间（ISO 8601 UTC） |
| `title_en` | string | 可空 | 英文标题 |
| `score` | int | 可空 | 重要性评分（0-100，越高越值得读） |
| `permalink` | string | 可空 | AIHOT 站内永久链接 |
| `selected` | bool | — | 是否精选（仅分页逻辑内部使用） |

### 分页与缓存

- **分页**：单次最多获取 100 条（`take=100`），自动通过 `cursor` 翻页直到最后一页
- **ETag 缓存**：首次请求保存响应 `ETag`，后续请求携带 `If-None-Match`；无新内容时 API 返回 304（空 body），节省 99% 带宽
- **时间窗口**：`since` 参数最早只能到 7 天前，更早会被 API 自动截断

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
