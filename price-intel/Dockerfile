FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 TZ=Asia/Ho_Chi_Minh

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt APScheduler

COPY . .
RUN python fixtures/make_fixtures.py || true

# Mặc định: lập lịch chạy pipeline (override sang 'python run_pipeline.py' để chạy 1 lần).
CMD ["python", "scheduler.py"]
