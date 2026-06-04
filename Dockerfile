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

# 앱 아이콘이 없으면 플레이스홀더 생성 (HF Spaces는 바이너리 파일 직접 저장 불가)
RUN python3 -c "from PIL import Image; import os; pub='frontend/public'; os.makedirs(pub,exist_ok=True); [Image.new('RGB',(s,s),color='#1C1008').save(f'{pub}/{n}','PNG') for s,n in [(512,'icon-512.png'),(192,'icon-192.png'),(180,'apple-touch-icon.png')] if not os.path.exists(f'{pub}/{n}')]"

# 프론트엔드 빌드
RUN cd frontend && npm install && npm run build

EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
