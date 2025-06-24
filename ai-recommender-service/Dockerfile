# 使用輕量級的 Python 映像
FROM python:3.9-slim-buster

# 設定工作目錄
WORKDIR /app

# 複製依賴文件並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 暴露 FastAPI 預設端口
EXPOSE 8000

# 啟動應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
