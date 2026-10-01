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

# CLIP 모델을 이미지에 미리 포함 (컨테이너가 깰 때마다 ~600MB 다운로드 방지).
# HF Spaces는 컨테이너를 uid 1000으로 실행하므로 모두가 읽을 수 있는 경로에 저장.
ENV HF_HOME=/opt/hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32')"     && chmod -R a+rwX /opt/hf_cache

COPY . .

# PWA 아이콘 재생성 (LFS 미해결 대비 — Pillow로 직접 생성)
RUN python3 generate_icons.py

# 프론트엔드 빌드
RUN cd frontend && npm install && npm run build

EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
