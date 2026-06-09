#!/bin/bash
# scripts/install.sh

set -e

echo "开始安装 AIHOT Tracker..."

# 检查 Python 版本
python3 --version || { echo "错误: 需要 Python 3.8+"; exit 1; }

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 创建目录
echo "创建数据目录..."
mkdir -p data logs

# 复制配置文件
if [ ! -f .env ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置 Webhook URL"
fi

# 初始化数据库
echo "初始化数据库..."
python -m src.main init

echo "安装完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件配置飞书 Webhook URL"
echo "2. 运行 'python -m src.main run --once' 测试"
echo "3. 运行 'sudo bash scripts/setup_service.sh' 配置系统服务"
