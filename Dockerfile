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

# PWA 아이콘 재생성 (LFS 미해결 대비 — Pillow로 직접 생성)
RUN python3 -c "\
from PIL import Image; import os, sys; \
src = 'frontend/icon.png'; \
if not os.path.exists(src): print('No icon.png'); sys.exit(0); \
try: \
    img = Image.open(src).convert('RGBA'); \
    for sz, p in [(192,'frontend/public/icon-192.png'),(512,'frontend/public/icon-512.png'),(180,'frontend/public/apple-touch-icon.png')]: \
        img.resize((sz,sz),Image.LANCZOS).save(p,'PNG'); \
        print(f'Icon {sz}x{sz} -> {p}') \
except Exception as e: print(f'Icon gen skipped: {e}') \
"

# 프론트엔드 빌드
RUN cd frontend && npm install && npm run build

EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
