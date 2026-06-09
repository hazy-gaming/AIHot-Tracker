FROM python:3.12-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY src/ ./src/
COPY config/ ./config/

# 创建数据和日志目录
RUN mkdir -p data logs

# 初始化数据库
RUN python -m src.main init

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "-m", "src.main", "run"]
