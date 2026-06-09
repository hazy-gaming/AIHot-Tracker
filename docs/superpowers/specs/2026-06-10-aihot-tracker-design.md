# AIHOT Tracker - AI 新闻实时推送系统设计文档

## 1. 项目概述

### 1.1 项目背景
AIHOT (https://aihot.virxact.com/) 是一个 AI 行业动态聚合网站，提供高质量的 AI 新闻、论文、产品更新等内容。用户希望能够实时追踪这些内容，并在更新时自动推送到飞书，以便及时获取最新信息。

### 1.2 项目目标
- 实时追踪 AIHOT 网站的 AI 新闻更新
- 发现新内容后自动推送到飞书
- 支持智能轮询，平衡实时性和稳定性
- 架构可扩展，未来支持微信等其他推送渠道

### 1.3 技术约束
- 运行环境：Linux 虚拟机
- 技术栈：Python 3.8+
- 数据库：SQLite（零配置）
- 进程管理：Systemd

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    调度层 (Cron/Systemd Timer)           │
│                    每 5 分钟触发一次                       │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    主程序 (main.py)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  API 客户端   │  │  去重管理器   │  │  消息格式化器  │     │
│  │  (fetcher)   │  │  (dedup)    │  │  (formatter) │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│         ▼                ▼                ▼             │
│  ┌─────────────────────────────────────────────────┐   │
│  │              SQLite 数据库 (去重存储)              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    推送层 (推送管理器)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  飞书推送器   │  │  微信推送器   │  │  更多渠道...  │     │
│  │  (feishu)    │  │  (wechat)   │  │  (extensible)│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 设计原则
1. **模块化**：每个组件职责单一，易于测试和维护
2. **可扩展**：推送层支持插件式添加新渠道
3. **幂等性**：重复执行不会重复推送
4. **容错性**：单次失败不影响后续执行

## 3. API 集成

### 3.1 官方 API 优势
- ✅ **无需爬虫**：直接调用官方 API，合法合规
- ✅ **无需认证**：匿名免费、无需 token
- ✅ **结构化数据**：JSON 格式，无需解析 HTML
- ✅ **时间筛选**：`since` 参数支持增量获取
- ✅ **支持分类**：可以按类别筛选推送

### 3.2 API 端点
```
GET https://aihot.virxact.com/api/public/items
```

**参数：**
- `mode`: `selected`（精选）或 `all`（全部）
- `since`: ISO-8601 时间戳，获取该时间之后的内容
- `category`: 分类筛选（可选）
- `q`: 关键词搜索（可选）

**示例：**
```bash
# 获取最近 5 分钟的新内容
curl "https://aihot.virxact.com/api/public/items?mode=selected&since=2026-06-10T14:25:00Z"
```

### 3.3 API 响应格式
```json
{
  "items": [
    {
      "id": "unique-id",
      "title": "GPT-5 即将发布",
      "url": "https://twitter.com/...",
      "summary": "OpenAI 宣布 GPT-5 将在下个月发布...",
      "category": "模型发布",
      "source": "Twitter",
      "published_at": "2026-06-10T14:30:00Z"
    }
  ],
  "total": 10,
  "has_more": false
}
```

## 4. 智能轮询策略

### 4.1 策略设计
```
┌─────────────────────────────────────────────────────────┐
│                    智能轮询策略                          │
├─────────────────────────────────────────────────────────┤
│  基础间隔：5 分钟                                        │
│                                                         │
│  动态调整：                                              │
│  - 发现新内容 → 立即推送，保持 5 分钟间隔                   │
│  - 连续 3 次无新内容 → 延长到 10 分钟                      │
│  - 连续 6 次无新内容 → 延长到 15 分钟                      │
│  - 发现新内容 → 重置为 5 分钟                              │
│                                                         │
│  极限优化：                                              │
│  - 工作时间（9:00-18:00）→ 5 分钟间隔                     │
│  - 非工作时间 → 15 分钟间隔                               │
└─────────────────────────────────────────────────────────┘
```

### 4.2 实际效果
- 网站更新后，**最多 5 分钟内**会推送
- 如果网站更新频繁，几乎感觉不到延迟
- 比固定 5 分钟轮询**节省 50-70% 的请求量**

### 4.3 配置参数
```yaml
polling:
  base_interval: 300          # 基础间隔：5 分钟（秒）
  min_interval: 60            # 最小间隔：1 分钟
  max_interval: 900           # 最大间隔：15 分钟
  empty_threshold: 3          # 连续空轮询 N 次后延长间隔
  work_hours:
    start: 9
    end: 18
    interval: 300             # 5 分钟
  off_hours_interval: 900     # 非工作时间：15 分钟
```

## 5. 数据存储和去重

### 5.1 SQLite 数据库设计

#### 已推送的内容表（核心去重）
```sql
CREATE TABLE pushed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT UNIQUE NOT NULL,           -- API 返回的唯一标识
    title TEXT NOT NULL,                    -- 标题
    url TEXT NOT NULL,                      -- 原文链接
    summary TEXT,                           -- 中文摘要
    category TEXT,                          -- 分类标签
    source TEXT,                            -- 来源（Twitter/RSS/Blog等）
    pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 推送时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 抓取时间
);
```

#### 推送日志表
```sql
CREATE TABLE push_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,                  -- 推送渠道（feishu/wechat）
    status TEXT NOT NULL,                   -- success/failed
    error_message TEXT,                     -- 失败原因
    items_count INTEGER,                    -- 本次推送条目数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 轮询状态表
```sql
CREATE TABLE poll_state (
    id INTEGER PRIMARY KEY,
    last_poll_at TIMESTAMP,                 -- 上次轮询时间
    last_new_item_at TIMESTAMP,             -- 上次发现新内容时间
    consecutive_empty INTEGER DEFAULT 0,    -- 连续空轮询次数
    current_interval INTEGER DEFAULT 300    -- 当前轮询间隔（秒）
);
```

### 5.2 去重流程
```
1. 调用 API: /api/public/items?since=上次轮询时间
2. 遍历返回的条目
3. 检查 item_id 是否已存在于 pushed_items 表
4. 如果不存在 → 插入数据库 → 推送到飞书
5. 如果已存在 → 跳过
6. 更新轮询状态
```

### 5.3 为什么用 SQLite？
1. ✅ **零配置**：无需安装数据库服务器
2. ✅ **单文件**：整个数据库就是一个文件
3. ✅ **适合 Linux**：系统自带，无需额外依赖
4. ✅ **性能足够**：每 5 分钟处理几十条数据绰绰有余

## 6. 飞书消息格式

### 6.1 消息卡片设计
```json
{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "🔥 AI 热点更新"
      },
      "template": "turquoise"
    },
    "elements": [
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**标题**\n[GPT-5 即将发布](https://example.com/twitter/123)"
        }
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**来源** | Twitter\n**分类** | 模型发布"
        }
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**摘要**\nOpenAI 宣布 GPT-5 将在下个月发布，性能提升 50%，支持多模态..."
        }
      },
      {
        "tag": "hr"
      },
      {
        "tag": "note",
        "elements": [
          {
            "tag": "plain_text",
            "content": "来自 AIHOT | 2026-06-10 14:30"
          }
        ]
      }
    ]
  }
}
```

### 6.2 多条内容合并推送
```
如果 5 分钟内有多条新内容：
- 1-3 条：逐条推送（每条一个卡片）
- 4-10 条：合并为一条消息（卡片列表）
- 10+ 条：合并推送 + 额外说明（"还有 N 条，请查看网站"）
```

### 6.3 推送效果示例
```
┌─────────────────────────────────────────┐
│  🔥 AI 热点更新                          │
├─────────────────────────────────────────┤
│  **标题**                                │
│  [GPT-5 即将发布](链接)                   │
│                                         │
│  **来源** | Twitter    **分类** | 模型发布  │
│                                         │
│  **摘要**                                │
│  OpenAI 宣布 GPT-5 将在下个月发布，       │
│  性能提升 50%，支持多模态...              │
│                                         │
│  ─────────────────────────────────────  │
│  来自 AIHOT | 2026-06-10 14:30          │
└─────────────────────────────────────────┘
```

## 7. 错误处理

### 7.1 错误分类和处理策略
```python
ERROR_TYPES = {
    "network": {           # 网络错误（超时、连接失败）
        "retry": True,     # 重试
        "max_retries": 3,
        "backoff": "exponential"  # 指数退避：1s, 2s, 4s
    },
    "rate_limit": {        # API 限流（429 错误）
        "retry": True,
        "max_retries": 1,
        "backoff": "fixed",
        "delay": 60        # 等待 60 秒
    },
    "api_error": {         # API 返回错误（4xx/5xx）
        "retry": False,    # 不重试
        "log": True,       # 记录日志
        "notify": True     # 发送告警到飞书
    },
    "push_failed": {       # 推送失败
        "retry": True,
        "max_retries": 2,
        "fallback": "log_to_file"  # 失败时写入本地文件
    }
}
```

### 7.2 日志设计
```
logs/
├── aihot_tracker.log          # 主日志（按天轮转）
├── aihot_tracker.log.1        # 昨天的日志
├── errors.log                 # 仅错误日志
└── push_history.log           # 推送历史（便于审计）
```

## 8. 配置管理

### 8.1 配置文件 (config.yaml)
```yaml
# 目标网站配置
source:
  api_url: "https://aihot.virxact.com/api/public/items"
  default_mode: "selected"
  default_category: null  # null 表示全部分类

# 轮询配置
polling:
  base_interval: 300          # 基础间隔：5 分钟（秒）
  min_interval: 60            # 最小间隔：1 分钟
  max_interval: 900           # 最大间隔：15 分钟
  empty_threshold: 3          # 连续空轮询 N 次后延长间隔
  work_hours:
    start: 9
    end: 18
    interval: 300             # 5 分钟
  off_hours_interval: 900     # 非工作时间：15 分钟

# 推送配置
push:
  channels:
    feishu:
      enabled: true
      webhook_url: "${FEISHU_WEBHOOK_URL}"  # 从环境变量读取
      secret: "${FEISHU_WEBHOOK_SECRET}"    # 签名密钥（可选）
    wechat:
      enabled: false         # 未来扩展
      webhook_url: ""

# 消息配置
message:
  max_items_per_message: 10   # 单条消息最多包含 N 条内容
  merge_threshold: 3          # 超过 N 条时合并推送
  include_summary: true       # 包含摘要
  include_source: true        # 包含来源
  include_category: true      # 包含分类

# 存储配置
storage:
  db_path: "./data/aihot_tracker.db"
  log_path: "./logs/aihot_tracker.log"
  backup_enabled: true
  backup_interval_days: 7     # 每 7 天备份一次
```

### 8.2 配置管理方式
1. **环境变量**：敏感信息（Webhook URL、密钥）从环境变量读取
2. **配置文件**：其他配置从 YAML 文件读取
3. **默认值**：所有配置都有合理的默认值
4. **热重载**：支持 SIGHUP 信号重载配置（无需重启）

## 9. 部署和运维

### 9.1 项目结构
```
aihot-tracker/
├── src/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── config.py            # 配置管理
│   ├── fetcher.py           # API 客户端
│   ├── dedup.py             # 去重管理器
│   ├── formatter.py         # 消息格式化器
│   ├── push/
│   │   ├── __init__.py
│   │   ├── base.py          # 推送基类（可扩展）
│   │   ├── feishu.py        # 飞书推送器
│   │   └── wechat.py        # 微信推送器（预留）
│   └── database.py          # 数据库管理
├── config/
│   └── config.yaml          # 配置文件
├── data/                    # 数据目录（SQLite）
├── logs/                    # 日志目录
├── scripts/
│   ├── install.sh           # 安装脚本
│   ├── setup_service.sh     # 配置 systemd 服务
│   └── backup.sh            # 备份脚本
├── requirements.txt         # Python 依赖
├── setup.py                 # 安装配置
└── README.md                # 使用文档
```

### 9.2 部署步骤
```bash
# 1. 克隆项目
git clone <repo-url>
cd aihot-tracker

# 2. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
export FEISHU_WEBHOOK_SECRET="your-secret"  # 可选

# 4. 修改配置（可选）
vim config/config.yaml

# 5. 初始化数据库
python -m src.main init

# 6. 测试运行
python -m src.main run --once  # 单次运行，测试是否正常

# 7. 配置 systemd 服务
sudo bash scripts/setup_service.sh

# 8. 启动服务
sudo systemctl start aihot-tracker
sudo systemctl enable aihot-tracker  # 开机自启
```

### 9.3 systemd 服务配置
```ini
[Unit]
Description=AIHOT Tracker - AI News Push Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/aihot-tracker
Environment=FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
ExecStart=/path/to/aihot-tracker/venv/bin/python -m src.main run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9.4 运维命令
```bash
# 查看状态
sudo systemctl status aihot-tracker

# 查看日志
sudo journalctl -u aihot-tracker -f

# 重启服务
sudo systemctl restart aihot-tracker

# 停止服务
sudo systemctl stop aihot-tracker

# 手动触发一次
python -m src.main run --once

# 查看统计
python -m src.main stats
```

### 9.5 监控和告警
```
┌─────────────────────────────────────────────────────────┐
│                    监控指标                              │
├─────────────────────────────────────────────────────────┤
│  1. 服务存活检查：每 5 分钟检查进程是否在运行              │
│  2. 推送成功率：连续失败 3 次发送告警                      │
│  3. 推送延迟：记录从内容发布到推送的时间差                  │
│  4. 存储空间：定期清理 30 天前的日志                       │
└─────────────────────────────────────────────────────────┘
```

### 9.6 依赖项 (requirements.txt)
```
requests>=2.28.0          # HTTP 请求
pyyaml>=6.0               # YAML 配置解析
schedule>=1.2.0           # 定时任务（可选，用于本地测试）
python-dotenv>=1.0.0      # 环境变量管理
```

## 10. 扩展性设计

### 10.1 推送渠道扩展
```python
# 推送基类
class BasePusher:
    def push(self, items: List[Item]) -> bool:
        raise NotImplementedError

# 飞书推送器
class FeishuPusher(BasePusher):
    def push(self, items: List[Item]) -> bool:
        # 实现飞书推送逻辑
        pass

# 微信推送器（预留）
class WechatPusher(BasePusher):
    def push(self, items: List[Item]) -> bool:
        # 实现微信推送逻辑
        pass
```

### 10.2 未来扩展方向
1. ✅ **微信推送**：已预留接口，实现 WechatPusher 即可
2. ✅ **钉钉推送**：实现 DingTalkPusher
3. ✅ **邮件推送**：实现 EmailPusher
4. ✅ **Telegram 推送**：实现 TelegramPusher
5. ✅ **内容过滤**：支持正则表达式过滤特定关键词
6. ✅ **内容翻译**：集成翻译 API，支持多语言推送

## 11. 总结

### 11.1 核心优势
1. ✅ **合法合规**：使用官方 API，无需爬虫
2. ✅ **近实时**：智能轮询，最多 5 分钟延迟
3. ✅ **可扩展**：模块化设计，易于添加新渠道
4. ✅ **易部署**：零配置数据库，一键部署
5. ✅ **高可靠**：完善的错误处理和恢复机制

### 11.2 预期效果
- 网站更新后，**最多 5 分钟内**推送到飞书
- 每天自动推送 **50-100 条** AI 新闻
- 系统运行稳定，**99.9%** 可用性
- 未来可轻松扩展到微信、钉钉等渠道

---

**文档版本**：v1.0
**创建日期**：2026-06-10
**作者**：AIHOT Tracker 项目组
