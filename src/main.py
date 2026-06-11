import argparse
import logging
import logging.handlers
import signal
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import Config
from src.database import Database
from src.fetcher import Fetcher
from src.rss_fetcher import RSSFetcher
from src.dedup import DedupManager
from src.push.feishu import FeishuPusher

def setup_logging(log_path: str):
    """设置日志（带轮转）"""
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件日志：最大 10MB，保留 5 个备份
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # 控制台日志
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )

def init_database(config: Config):
    """初始化数据库"""
    db_dir = Path(config.storage_db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    db = Database(config.storage_db_path)
    logging.info(f"数据库初始化完成: {config.storage_db_path}")
    return db

def run_once(config: Config, db: Database, dedup: DedupManager, fetcher=None):
    """执行一次轮询"""
    logger = logging.getLogger(__name__)

    # 获取上次轮询时间
    last_poll = db.get_last_poll_time()
    if last_poll is None:
        last_poll = datetime.now(timezone.utc) - timedelta(minutes=5)

    logger.info(f"开始轮询，上次轮询时间: {last_poll}")

    # 获取新条目（优先使用 RSS，更实时）
    if fetcher is None:
        if config.rss_url:
            fetcher = RSSFetcher(config.rss_url)
        else:
            fetcher = Fetcher(config.source_api_url, config.source_default_mode)

    items = fetcher.fetch_items(since=last_poll)
    logger.info(f"获取到 {len(items)} 个条目")

    # 去重
    new_items = dedup.filter_new_items(items)
    logger.info(f"过滤后 {len(new_items)} 个新条目")

    # 推送
    if new_items:
        if not config.feishu_enabled:
            logger.warning("飞书推送已禁用，跳过推送")
            return len(new_items)

        webhook_url = config.feishu_webhook_url
        if not webhook_url:
            logger.error("飞书 Webhook URL 未配置，请设置 FEISHU_WEBHOOK_URL 环境变量")
            return 0

        pusher = FeishuPusher(
            webhook_url=webhook_url,
            secret=config.feishu_webhook_secret,
            include_summary=config.message_include_summary,
            include_source=config.message_include_source,
            include_category=config.message_include_category,
            max_items=config.message_max_items
        )

        success = pusher.push(new_items)
        if success:
            logger.info(f"推送成功: {len(new_items)} 个条目")
            db.log_push("feishu", "success", items_count=len(new_items))

            # 标记为已推送
            for item in new_items:
                dedup.mark_as_pushed(item)

            # 重置连续空轮询计数
            db.update_consecutive_empty(0)
            db.update_last_new_item_time(datetime.now(timezone.utc))

            # 推送成功时更新轮询时间
            db.update_poll_state(datetime.now(timezone.utc))
        else:
            logger.error("推送失败")
            db.log_push("feishu", "failed", error_message="推送失败", items_count=0)
            # 推送失败时不更新轮询时间，保留原始时间以便重试
    else:
        logger.info("没有新条目")
        consecutive_empty = db.get_consecutive_empty() + 1
        db.update_consecutive_empty(consecutive_empty)

        # 动态调整轮询间隔
        if consecutive_empty >= config.polling_empty_threshold:
            current_interval = db.get_current_interval()
            new_interval = min(current_interval * 2, config.polling_max_interval)
            db.update_current_interval(new_interval)
            logger.info(f"连续 {consecutive_empty} 次空轮询，调整间隔为 {new_interval} 秒")

        # 只有 API 返回了条目（但都已推送过）才更新轮询时间
        # API 返回 0 条时不更新，保留上次时间以便下次覆盖该时间段
        if items:
            db.update_poll_state(datetime.now(timezone.utc))

    return len(new_items)

def run_scheduler(config: Config, db: Database):
    """运行调度器"""
    logger = logging.getLogger(__name__)
    logger.info("启动调度器")
    logger.info("按 Ctrl+C 停止服务")

    # 创建 DedupManager 实例并复用
    dedup = DedupManager(db)

    # 创建 Fetcher 实例并复用
    if config.rss_url:
        fetcher = RSSFetcher(config.rss_url)
    else:
        fetcher = Fetcher(config.source_api_url, config.source_default_mode)

    running = True

    def signal_handler(signum, frame):
        nonlocal running
        logger.info("收到停止信号，正在退出...")
        running = False

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 使用短间隔循环，以便更快响应停止信号
        while running:
            try:
                # 检查工作时间
                now = datetime.now(timezone.utc)
                if config.polling_work_hours_start <= now.hour < config.polling_work_hours_end:
                    interval = config.polling_work_hours_interval
                else:
                    interval = config.polling_off_hours_interval

                # 使用数据库中的当前间隔
                current_interval = db.get_current_interval()
                interval = min(current_interval, interval)

                logger.info(f"下次轮询在 {interval} 秒后")

                # 分段等待，每秒检查一次是否需要退出
                wait_start = time.time()
                while running and (time.time() - wait_start) < interval:
                    time.sleep(1)  # 每秒检查一次

                if not running:
                    break

                # 执行轮询
                run_once(config, db, dedup, fetcher)

            except Exception as e:
                logger.error(f"轮询出错: {e}", exc_info=True)
                time.sleep(10)
    finally:
        db.close()
        logger.info("调度器已停止")

def show_stats(db: Database):
    """显示统计信息"""
    last_poll = db.get_last_poll_time()
    consecutive_empty = db.get_consecutive_empty()
    current_interval = db.get_current_interval()

    print(f"上次轮询时间: {last_poll or '从未'}")
    print(f"连续空轮询次数: {consecutive_empty}")
    print(f"当前轮询间隔: {current_interval} 秒")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AIHOT Tracker - AI 新闻实时推送系统")
    parser.add_argument("command", choices=["init", "run", "stats"], help="命令")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--config", help="配置文件路径")

    args = parser.parse_args()

    # 加载配置
    config = Config(config_path=args.config)

    # 设置日志
    setup_logging(config.storage_log_path)

    # 初始化数据库
    db = init_database(config)

    if args.command == "init":
        print("数据库初始化完成")

    elif args.command == "run":
        dedup = DedupManager(db)
        if config.rss_url:
            fetcher = RSSFetcher(config.rss_url)
        else:
            fetcher = Fetcher(config.source_api_url, config.source_default_mode)

        if args.once:
            count = run_once(config, db, dedup, fetcher)
            print(f"完成，推送了 {count} 个条目")
        else:
            run_scheduler(config, db)

    elif args.command == "stats":
        show_stats(db)

    db.close()

if __name__ == "__main__":
    main()
