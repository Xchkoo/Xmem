FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 是否使用国内镜像源（默认 true，境内构建更快）。
# CI 在海外 runner 上构建时传 CN_MIRROR=false，直接走 deb.debian.org / PyPI 官方源，
# 避免跨洋访问阿里云、清华镜像导致的构建超时。
ARG CN_MIRROR=true

# 配置使用国内镜像源以加速下载
# 优先使用阿里云镜像（对测试版支持更好），如果失败可尝试其他镜像
RUN if [ "$CN_MIRROR" = "true" ]; then \
        if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
            sed -i 's|https://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
            sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
            sed -i 's|mirrors.tuna.tsinghua.edu.cn|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
        elif [ -f /etc/apt/sources.list ]; then \
            sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list && \
            sed -i 's|https://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list && \
            sed -i 's|mirrors.tuna.tsinghua.edu.cn|mirrors.aliyun.com|g' /etc/apt/sources.list; \
        fi; \
    fi

# 安装系统依赖：使用 --no-install-recommends 减少内存占用
# 并立即清理缓存以释放内存
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    libtesseract-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 使用 uv 安装依赖，避免跨平台 requirements 带来的不兼容包
# 索引源同样可被构建参数覆盖：CI 传 https://pypi.org/simple，境内默认走阿里云
ARG UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG UV_EXTRA_INDEX_URL="https://pypi.mirrors.ustc.edu.cn/simple/ https://pypi.org/simple"
ENV UV_INDEX_URL=${UV_INDEX_URL}
ENV UV_EXTRA_INDEX_URL=${UV_EXTRA_INDEX_URL}
ENV PATH="/app/.venv/bin:/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --timeout 120 --retries 5 uv && \
    uv sync --frozen --no-dev --no-install-project

# 复制应用代码
COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic
COPY init_db.py .
COPY ensure_db.py .

# 创建上传目录
RUN mkdir -p /app/uploads/images /app/uploads/files

# 创建非 root 用户用于 Celery（修复安全警告）
RUN useradd -m -u 1000 celeryuser && \
    chown -R celeryuser:celeryuser /app && \
    chmod -R 755 /app/uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

