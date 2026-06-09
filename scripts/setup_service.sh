#!/bin/bash
# scripts/setup_service.sh

set -e

SERVICE_NAME="aihot-tracker"
INSTALL_DIR=$(pwd)
VENV_DIR="$INSTALL_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
MAIN_SCRIPT="$VENV_DIR/lib/python*/site-packages/src/main.py"

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

echo "配置 systemd 服务..."

# 创建服务文件
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=AIHOT Tracker - AI News Push Service
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$PYTHON_BIN -m src.main run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
systemctl daemon-reload

# 启用服务
systemctl enable $SERVICE_NAME

echo "服务配置完成！"
echo ""
echo "启动服务: sudo systemctl start $SERVICE_NAME"
echo "查看状态: sudo systemctl status $SERVICE_NAME"
echo "查看日志: sudo journalctl -u $SERVICE_NAME -f"
