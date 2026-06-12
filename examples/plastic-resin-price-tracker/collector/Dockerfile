FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mac dinh chay scheduler (lap lich tuan). Doi sang `python run.py` de chay 1 lan.
CMD ["python", "scheduler.py"]
