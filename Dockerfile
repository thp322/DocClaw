FROM python:3.11-slim

WORKDIR /app

# 先单独拷贝依赖清单，利用 Docker 层缓存：requirements 不变时跳过 pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝项目代码
COPY . .

EXPOSE 8501

# Streamlit 健康检查端点：/_stcore/health
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# 监听 0.0.0.0 才能被容器外的 nginx-proxy 访问
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
