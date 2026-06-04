FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 + Node.js (프론트 빌드용)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgomp1 libgl1-mesa-dri libglx-mesa0 libgl1 \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# 백엔드 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 프론트엔드 빌드
RUN cd frontend && npm install && npm run build

EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
