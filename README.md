---
title: Inner Gallery Api
emoji: 🖼️
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: AI-powered art reflection journal with computer vision and grounded LLM
---

<br />
<img width="2123" height="724" alt="Inner Gallery header" src="https://github.com/user-attachments/assets/c1d664e8-10f2-4183-a0de-f9f486f2cb30" />

<div align="center">

# Inner Gallery

### 작품을 통해 오늘의 마음을 기록하는 AI 아트 저널

**Computer Vision · Multimodal AI · Grounded AI Docent · Art Reflection Journal**

<br />
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-Frontend-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![OpenCV](https://img.shields.io/badge/OpenCV-CV_Pipeline-5C3EE8?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-4B8BBE?style=flat-square)](https://faiss.ai)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Docker](https://img.shields.io/badge/Docker-Deployment-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=flat-square&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/License-MIT-C9A84C?style=flat-square)](LICENSE)
<br />

**Inner Gallery is a multimodal AI art reflection journal that recognizes artworks, analyzes visual elements, and turns the viewing experience into a grounded personal reflection archive.**

**사용자가 작품을 촬영하거나 업로드하면, 작품 인식·색채/구도/여백 분석·감정 회고·저널 저장까지 이어지는 AI 기반 아트 저널 서비스입니다.**

</div>

---

## Table of Contents

- [Project Intent](#project-intent)
- [What I Built](#what-i-built)
- [Why It Matters](#why-it-matters)
- [Key Contributions](#key-contributions)
- [Product Experience](#product-experience)
- [System Architecture](#system-architecture)
- [Core Features](#core-features)
- [Grounded AI & Safety](#grounded-ai--safety)
- [Tech Stack](#tech-stack)
- [Data Assets](#data-assets)
- [API Overview](#api-overview)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Engineering Challenges](#engineering-challenges)
- [Future Improvements](#future-improvements)
- [References & Licenses](#references--licenses)

---

## Project Intent

Most art-guide applications are built around **identification and explanation**: title, artist, period, and historical context. Inner Gallery started from a different question.

> What if an artwork could become a mirror for today's emotions, not just an object to be explained?

미술 감상에서 오래 기억에 남는 순간은 작품 정보를 많이 알 때만 생기지 않습니다. 어떤 색은 마음을 누그러뜨리고, 어떤 구도는 고요함을 만들며, 어떤 여백은 현재의 감정을 다시 바라보게 합니다.

Inner Gallery는 이 경험을 기술적으로 구현하기 위해 만든 프로젝트입니다. 사용자가 작품 이미지를 촬영하거나 업로드하면, 시스템은 작품을 식별하고 시각 요소를 분석한 뒤 사용자의 감정 상태와 연결된 해설, 질문, 스케치 회고, 전시 티켓 형태의 저널을 생성합니다.

이 프로젝트에서 가장 중요하게 설계한 원칙은 두 가지입니다.

1. **감성적인 AI 글쓰기가 근거 없는 해설로 흐르지 않게 만들 것**  
   작품 식별 결과, 컴퓨터 비전 분석값, 직접 구축한 작품 맥락 DB를 기반으로 해설을 생성하고, 불확실한 시각 주장은 프롬프트에서 제외했습니다.

2. **감상 이후의 마음 변화가 사라지지 않게 기록화할 것**  
   작품 정보, 감정 키워드, 마음색, 감상 질문, 스케치, AI 회고문을 하나의 전시 티켓처럼 저장해 개인적인 아카이브로 남기도록 설계했습니다.

> Inner Gallery는 작품을 설명하는 AI가 아니라,  
> **작품을 통해 나를 돌아보게 하는 AI**입니다.

> **Note**  
> 본 프로젝트는 의료적 치료나 심리 진단을 제공하지 않습니다. 아트테라피의 감상 방식에서 영감을 받아, 작품의 시각 요소를 통해 감정을 언어화하고 기록하는 경험을 제공합니다.

---

## What I Built

Inner Gallery는 단순히 외부 API를 호출하는 데모가 아니라, **명화 감상이라는 도메인에 맞춘 데이터 자산, 컴퓨터 비전 파이프라인, LLM grounding 전략, 풀스택 저널 UX**를 직접 설계한 서비스입니다.

### Highlights

| Area | Implementation |
|---|---|
| **Artwork Recognition** | CLIP ViT-B/32 + FAISS, Gemini Vision, Google Web Detection, OCR 힌트를 조합한 4-Way hybrid validation |
| **Computer Vision** | 작품 프레임 감지, perspective warp, LAB KMeans 색채 분석, 구도·여백·대칭성·saliency·인물 분석 |
| **Grounded AI Docent** | `safe_visual_facts`와 검증된 작품 맥락 DB를 기반으로 도슨트 해설 생성 |
| **Emotion Reflection UX** | 감상 전/후 감정 키워드, 8차원 감정 벡터, 마음색, 마음 스케치, 감상 질문 |
| **Journal Archive** | 감상 결과를 전시 티켓 형태로 저장하고 이미지로 저장·공유 |
| **Daily Curation** | AIC Public Domain API 기반 오늘의 명화, 국내외 전시 정보, 예술가 명언 큐레이션 |
| **Full-stack Delivery** | React + Vite PWA, FastAPI backend, SQLite/Supabase PostgreSQL, Docker, Hugging Face Spaces 배포 |

---

## Why It Matters

Inner Gallery는 작품 인식 기능을 기반으로, 사용자가 작품을 감상하고 자신의 감정을 기록하는 과정을 지원하는 서비스입니다. 작품명 추정은 정확한 감상 맥락을 제공하기 위한 단계이며, 이후의 색채·구도 분석, 감정 키워드 선택, 저널 기록으로 이어지도록 설계했습니다.

이 프로젝트의 핵심은 다음 세 가지를 하나의 사용자 경험으로 연결하는 것입니다.

```text
Artwork Recognition
        ↓
Visual Evidence Extraction
        ↓
Emotion-aware Reflection
        ↓
Personal Journal Archive
```

따라서 Inner Gallery는 작품 정보 제공에 그치지 않고, **시각 분석 → 정서적 해석 → 자기 회고 → 기록화**로 이어지는 감상 흐름을 구현합니다.

---

## Key Contributions

이 프로젝트에서 직접 설계하고 구현한 주요 작업입니다.

| Contribution | Details |
|---|---|
| **Product Planning** | “작품 해설”이 아니라 “자기 회고”로 이어지는 AI 아트 저널 콘셉트 설계 |
| **UX Design** | 감상 전 감정 선택 → AI 도슨트 → 감상 질문 → 마음 스케치 → 감상 후 감정 기록 → 티켓 아카이브로 이어지는 플로우 설계 |
| **CV Pipeline Engineering** | 작품 프레임 검출, 화질 검사, 원근 보정, 색채·구도·saliency·인물 분석 파이프라인 구현 |
| **Multimodal AI Integration** | CLIP/FAISS, Gemini Vision, Google Web Detection, OCR 힌트를 결합한 작품 식별 로직 구현 |
| **LLM Grounding** | 불확실한 시각 주장 차단, 검증된 visual facts 기반 해설 생성, unsupported claim 검증 설계 |
| **Data Engineering** | 18,455개 작품 FAISS 인덱스, 작품 메타데이터, 6,905줄 규모의 작품 맥락 DB, 작가 명언 데이터 구축 |
| **Full-stack Development** | FastAPI API 서버, React SPA/PWA, JWT 인증, 저널 CRUD, 이미지 저장·공유 기능 구현 |
| **Deployment** | Docker 기반 Hugging Face Spaces 배포, SQLite/Supabase PostgreSQL 자동 전환 구조 설계 |

---

## Product Experience

### End-to-End Flow

```text
이미지 업로드 / 카메라 촬영
        ↓
[카메라 전용] 화질 검사 → 작품 프레임 감지 → 크롭 → 원근 보정
        ↓
CLIP+FAISS · Gemini Vision · Google Web Detection · OCR 힌트
        ↓
4-Way 하이브리드 작품 식별
        ↓
색채 · 구도 · 인물 · Saliency 병렬 분석
        ↓
사용자 감정 상태 입력
        ↓
Grounded AI 도슨트 해설 + 감상 질문 + 마음색 제안
        ↓
도슨트 채팅 / 사조·시대 맥락 조회 / 감상 질문 답변
        ↓
마음 스케치 → Gemini Vision 기반 회고문 생성
        ↓
감상 후 감정 키워드 선택
        ↓
전시 티켓 형태로 저장 → Inner Gallery Archive
        ↓
[별도] 오늘의 명화 / 전시 정보 / 예술가 명언 큐레이션
```

```mermaid
flowchart TD
    A[Artwork Image Upload / Camera] --> B{Camera Mode?}
    B -->|Yes| C[Quality Check\nBlur / Glare / Brightness]
    B -->|No| D[Frame Detection\n& Perspective Warp]
    C --> D
    D --> E[Hybrid Artwork Recognition]
    E --> E1[CLIP ViT-B/32 + FAISS]
    E --> E2[Gemini 2.0 Flash Vision]
    E --> E3[Google Web Detection]
    E --> E4[OCR Hint Injection]
    E --> F[Computer Vision Analysis]
    F --> F1[LAB KMeans Color]
    F --> F2[Composition & Saliency]
    F --> F3[Person & Posture]
    F --> G[8D Emotion Vector]
    G --> H[Grounded AI Docent]
    H --> I[Reflection Questions]
    H --> J[Docent Chat]
    I --> K[Mind Sketch]
    K --> L[Sketch Reflection]
    L --> M[Journal Ticket Archive]
    N[Daily Artwork / Exhibitions / Quotes] --> M
```

---

## System Architecture

```mermaid
flowchart TD
    subgraph CLIENT["Client / React PWA"]
        A1["Upload · Camera · Results"]
        A2["Drawing · Routine · Journal"]
        A3["Emotion Input · Docent Chat · Auth"]
    end

    subgraph BACKEND["FastAPI Backend / Docker"]
        B1["REST API Endpoints"]
        B2["JWT Auth · Journal CRUD"]
        B3["AI / CV Orchestration"]
        B4["External API Integration"]
    end

    subgraph AI_CV["AI / Computer Vision Pipeline"]
        C1["Roboflow Frame Detection"]
        C2["OpenCV Preprocessing"]
        C3["CLIP ViT-B/32 + FAISS"]
        C4["Gemini 2.0 Flash Vision"]
        C5["Google Cloud Vision"]
    end

    subgraph EXTERNAL["External Data APIs"]
        D1["Art Institute of Chicago API"]
        D2["KCISA Exhibition API"]
    end

    subgraph DATABASE["Database Layer"]
        E1["SQLite Local / HF Spaces"]
        E2["Supabase PostgreSQL Optional"]
        E3["users · journal_entries"]
        E4["artworks · artists · quotes"]
        E5["password_reset_tokens"]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1

    B1 --> B2
    B1 --> B3
    B1 --> B4

    B3 --> C1
    B3 --> C2
    B3 --> C3
    B3 --> C4
    B3 --> C5

    B4 --> D1
    B4 --> D2

    B2 --> E1
    B2 --> E2
    B2 --> E3
    B2 --> E4
    B2 --> E5
```

---

## Core Features

### 1. Artwork Recognition — 4-Way Hybrid Validation

작품 식별은 단일 모델의 결과에 의존하지 않고, 네 가지 인식 경로를 교차 검증합니다.

| Engine | Role |
|---|---|
| **CLIP ViT-B/32 + FAISS** | 18,455개 명화 이미지 로컬 벡터 인덱스 기반 유사도 검색. L2 normalization 후 IndexFlatIP로 cosine similarity 검색 |
| **Gemini 2.0 Flash Vision** | 작품명, 작가, 연도 후보 추출 및 이미지 내 OCR/시각 요소 분석 |
| **Google Cloud Vision Web Detection** | 미술관, 위키피디아 등 웹상의 신뢰 도메인 기반 교차 검증 |
| **OCR Hint Injection** | 전시장 작품 라벨의 제목·작가 텍스트를 추출해 strong / partial / rejected 힌트로 분류 |

식별 결과는 `confirmed`, `internal_match`, `web_confirmed`, `unknown` 상태로 분류됩니다. 신뢰도가 낮은 경우 작품명을 억지로 단정하지 않고, 색채·구도 중심의 감상 경험으로 전환합니다.

---

### 2. Computer Vision Pipeline

LLM에 이미지를 바로 전달하지 않고, 먼저 해설의 근거가 되는 시각 정보를 추출합니다.

#### Input Quality Check

카메라 촬영 모드에서는 흐림, 어두움, 반사광, 작품 크기를 검사해 분석 품질을 높입니다.

| Check | Algorithm | Threshold |
|---|---|---|
| Blur | Laplacian variance | `< 75.0` |
| Darkness | Average brightness | `< 0.12` |
| Glare | Bright pixel ratio + largest blob | `> 8%` or blob `> 1.5%` |
| Artwork size | bbox / image area | `< 15%` |

이미지 업로드 모드에서는 사용자가 직접 선택한 이미지에 대해 불필요한 경고가 뜨지 않도록 화질 경고를 비활성화했습니다.

#### Frame Detection & Perspective Warp

```python
# Dynamic Canny threshold
v = np.median(blur)
edges = cv2.Canny(blur, lower=0.67 * v, upper=1.33 * v)

# Convex quadrilateral detection → Homography
M = cv2.getPerspectiveTransform(src_corners, dst_corners)
warped = cv2.warpPerspective(img, M, (target_w, target_h))
```

사각형 윤곽 검출에 실패하면 8% padding crop으로 fallback하고, 원본과 crop 이미지를 함께 분석하는 dual-image 전략으로 인식 안정성을 높였습니다.

#### Visual Feature Extraction

| Area | Implementation |
|---|---|
| **Color** | CIE LAB 색공간에서 KMeans(k=5)로 주조색 추출, RGB/HSV/점유율 계산 |
| **Custom Color Rules** | 무채색 필터링, Gold/Amber 별도 분류, 밝은 영역 위치 추적 |
| **Composition** | 9분할 위치, 여백 비율, 대칭성, 피사체 규모, edge direction 분석 |
| **Saliency** | OpenCV StaticSaliencySpectralResidual + 대비 기반 fallback |
| **Person Analysis** | HOG, Haar Cascade, 피부색 fallback 기반 인물/자세 분석 |

---

### 3. Emotion Map — 8D Emotion Vector

색채, 구도, 인물, saliency 분석 결과와 사용자가 선택한 감정 키워드를 조합해 8가지 감정 차원을 계산합니다.

| Emotion | Main Signals |
|---|---|
| 안정감 | 저채도, 높은 대칭성, 적절한 여백 |
| 고독감 | 어두운 톤, 차가운 색, 넓은 여백, 작은 피사체 |
| 긴장감 | 높은 명암 대비, 고채도, 비대칭 구도 |
| 따뜻함 | 따뜻한 색 비율, 높은 밝기 |
| 슬픔 | 어두움, 저채도, 차가운 색, 위축된 자세 |
| 생동감 | 밝음, 고채도, 따뜻한 색, 활기 있는 자세 |
| 경이로움 | 강한 saliency 집중, 복잡한 구도, 넓은 색조 범위 |
| 멜랑콜리 | 낮은 채도 + 부드러운 색 + 인물 고독 자세 조합 |

감정 판단은 단순 임계값이 아니라 복합 조건으로 보정했습니다. 예를 들어 밝고 차가운 색은 고독감이 아니라 평온함으로 해석하고, 밝고 열린 여백은 고독이 아닌 해방감으로 반영합니다.

---

### 4. Grounded AI Docent

AI 도슨트는 다음 정보를 기반으로 해설을 생성합니다.

- `safe_visual_facts`: 신뢰도 높은 시각 분석 결과
- `blocked_uncertain_facts`: 추측이 금지된 불확실한 항목
- 직접 구축한 작품 맥락 DB (`artwork_era_db.json`)
- 8차원 감정 벡터 및 사용자 감정 상태
- 사용자가 선택한 해설 스타일 및 분석 포커스

해설은 항상 다음 구조를 따릅니다.

```text
1. 시각 분석    색채·구도·여백·인물 요소 묘사
2. 정서적 작용  시각 요소가 감상자에게 줄 수 있는 감각 설명
3. 자기 회고   작품을 통해 자신의 마음을 돌아보는 질문 제안
```

지원하는 해설 스타일은 `아트 테라피`, `도슨트 해설`, `시각 분석`, `짧은 감상`입니다.

---

### 5. Reflection Journal UX

Inner Gallery의 저널 기능은 단순 저장 기능이 아니라 감상 경험을 하나의 개인 아카이브로 만드는 핵심 UX입니다.

#### Emotion Keyword Selection

감상 전후의 감정을 별도로 기록해 작품 경험으로 인한 정서 변화를 추적합니다.

| Group | Examples |
|---|---|
| 가라앉음 | 슬픔, 외로움, 그리움, 공허함, 상처, 후회, 무기력 |
| 불안과 흔들림 | 불안, 긴장감, 두려움, 막연함, 내적 갈등 |
| 분노와 복잡한 감정 | 짜증, 화, 증오, 애증 |
| 안정과 위로 | 평온함, 편안함, 여유, 온기, 위로, 수용, 화해 |
| 회복과 긍정 | 회복, 희망, 기쁨, 설렘, 자신감, 열정, 자유로움, 영감 |
| 깊은 감각과 바라봄 | 감동, 경이로움, 성찰, 집중, 깨달음, 통찰 |

#### Mind Sketch

감상 후 HTML5 Canvas에 마음의 흔적을 남길 수 있습니다.

| Mode | Description |
|---|---|
| 선으로 남기기 | 감정의 방향을 선과 형태로 표현 |
| 색으로 채우기 | 감정에 가까운 색으로 캔버스를 채움 |
| 문장 쓰기 | 작품이 건넨 말을 짧게 기록 |

Gemini Vision이 스케치의 선, 색, 여백을 읽고 2~3문장 또는 4항목의 회고문을 생성합니다.

#### Mood Color

감상 후 감정을 색으로 기록합니다.

- 작품 분석 팔레트에서 선택
- 감정-색 매핑 기반 자동 제안
- HSL 슬라이더로 직접 색상 조정
- 선택한 마음색과 이름을 저널에 저장

#### Ticket Archive

감상 기록은 `No. IG-YYMMDD-XXXX` 형식의 전시 티켓으로 저장됩니다.

| Field | Content |
|---|---|
| 작품 정보 | 제목, 작가, 제작 연도 |
| AI 해설 | 에세이 본문, 감상 질문, 위로 메시지 |
| 감정 데이터 | 감상 전후 감정 키워드, 마음색, 무드 태그 |
| 사용자 기록 | 감상 후기, 질문 답변, 전시 메모 |
| 스케치 | 마음 스케치 이미지, 제목, 회고문 |
| 시대 정보 | 작품 사조, 역사적 맥락, 작가 생애 |
| 썸네일 | 작품 썸네일 이미지 |

티켓은 `html-to-image`로 PNG 저장이 가능하며, 외부 이미지 CORS 문제를 줄이기 위해 이미지를 data URL로 변환한 뒤 렌더링합니다.

---

### 6. Daily Curation

#### 오늘의 명화

Art Institute of Chicago Public Domain Collection API를 통해 매일 다른 퍼블릭 도메인 명화를 제공합니다.

- 날짜 기반 결정론적 작품 선택
- AIC IIIF Image API를 통한 고화질 이미지 제공
- Gemini 기반 한국어 설명 번역
- 감상 질문 제시 및 답변 저널 저장

#### 오늘의 전시 산책

국내외 미술 기관 전시 정보를 통합 제공합니다.

| Source | Content |
|---|---|
| 국립문화정보원 KCISA API | 국립현대미술관 등 국내 기관 전시 정보 |
| 예술의전당 API | 현재 진행 전시 |
| Art Institute of Chicago | AIC 현재 전시 정보 |

#### 예술가의 한 문장

세계 주요 예술가 120+명의 명언을 한국어와 영어로 제공합니다.

---

## Grounded AI & Safety

Inner Gallery는 LLM의 감성적 글쓰기가 근거 없는 해설로 흐르지 않도록 다음 안전장치를 두었습니다.

| Risk | Design Response |
|---|---|
| 작품명을 잘못 단정할 수 있음 | 4-Way hybrid validation과 confidence status로 식별 결과를 분류 |
| 보이지 않는 표정·시선·행동을 상상할 수 있음 | `safe_visual_facts`와 `blocked_uncertain_facts`를 분리해 불확실한 주장을 차단 |
| 추상화·정물에 인물 감정을 잘못 부여할 수 있음 | 작품 유형에 따라 인물 분석 자동 비활성화 |
| 감상문이 심리 진단처럼 보일 수 있음 | 의료·치료·진단 표현 금지, 가능성 중심의 완곡한 표현 사용 |
| 생성 결과가 시각 근거를 벗어날 수 있음 | unsupported visual claim 검증 및 필요 시 재생성 |

---

## Tech Stack

| Area | Stack |
|---|---|
| **Frontend** | React 18, Vite, React Router v6, HTML5 Canvas, Vanilla CSS, Axios |
| **PWA** | Web App Manifest, Service Worker ready, apple-touch-icon, theme-color |
| **Backend** | Python 3.11, FastAPI, Uvicorn, JWT (`python-jose`), bcrypt |
| **Database** | SQLite / Supabase PostgreSQL (`DATABASE_URL` 환경변수 기반 자동 전환) |
| **Computer Vision** | OpenCV, Roboflow Serverless, KMeans, HOG, Haar Cascade, Saliency Map, Perspective Transform |
| **AI / ML** | Gemini 2.0 Flash, Google Cloud Vision API, CLIP ViT-B/32, FAISS IndexFlatIP, scikit-learn, NumPy |
| **External APIs** | Art Institute of Chicago Public API, AIC IIIF Image API, KCISA API |
| **Deployment** | Docker, Hugging Face Spaces, port 7860 |
| **Data** | `artwork_era_db.json`, `index.faiss`, `metadata.json`, `artist_quotes` |

---

## Data Assets

| Asset | Description |
|---|---|
| `artwork_era_db.json` | 작품별 사조, 제작 배경, 시대 맥락, 작가 생애, 시각적 연결 정보를 담은 6,905줄 규모의 큐레이션 DB |
| `index.faiss` | 18,455개 명화 이미지를 CLIP ViT-B/32로 임베딩한 로컬 벡터 검색 인덱스 |
| `metadata.json` | FAISS 검색 결과와 연결되는 작품명, 작가, 장르, 연도 등 메타데이터 |
| `artist_quotes` | 세계 주요 예술가 120+명의 명언 데이터. 한국어·영문 병행 수록 |
| `backend/scripts/` | 데이터셋 전처리, FAISS 인덱스 빌드, 작가 정보 임포트, DB 검증 및 마이그레이션 스크립트 |

> 원본 Kaggle 이미지 데이터셋은 저장소에 포함하지 않고, 스크립트를 통해 로컬에서 FAISS 인덱스를 재현할 수 있도록 구성했습니다.

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | 이미지 전체 분석 파이프라인 실행 |
| `POST` | `/api/quick-match` | 업로드 즉시 Top-5 작품 후보 미리보기 |
| `POST` | `/api/quick-quality` | 카메라 모드 전용 화질 사전 검사 |
| `POST` | `/api/sketch-reflection` | 마음 스케치 이미지 기반 AI 회고문 생성 |
| `POST` | `/api/essay-text` | 작품 정보 기반 도슨트 에세이 재생성 |
| `POST` | `/api/artwork-era` | 작품 사조·시대·작가 맥락 조회 |
| `POST` | `/api/docent-chat` | 작품 컨텍스트 기반 도슨트 채팅 |
| `POST` | `/api/translate` | 영어 작품 설명 한국어 번역 |
| `GET` | `/api/daily-artwork` | 오늘의 명화 추천 |
| `GET` | `/api/artist-quote` | 예술가 명언 랜덤 반환 |
| `GET` | `/api/exhibitions` | 국내외 전시 정보 조회 |
| `GET` | `/api/journal` | 감상 기록 목록 조회 |
| `POST` | `/api/journal/thumbs` | 날짜 목록 기반 썸네일 배치 조회 |
| `GET` | `/api/journal/detail/{date}` | 감상 기록 상세 조회 |
| `POST` | `/api/journal` | 감상 기록 저장 |
| `DELETE` | `/api/journal/{date}` | 감상 기록 삭제 |
| `PATCH` | `/api/journal/{date}/note` | 티켓 메모 수정 |
| `PATCH` | `/api/journal/{date}/exhibition` | 티켓 전시 제목 수정 |
| `PATCH` | `/api/journal/{date}/sketch` | 마음 스케치 데이터 업데이트 |
| `POST` | `/api/auth/register` | 회원가입 |
| `POST` | `/api/auth/login` | 로그인 및 JWT 발급 |
| `GET` | `/api/auth/me` | 현재 사용자 정보 조회 |
| `DELETE` | `/api/auth/me` | 계정 탈퇴 및 저널 데이터 삭제 |
| `POST` | `/api/auth/reset-password` | 비밀번호 재설정 |

---

## Database Schema

```mermaid
erDiagram
    users {
        INTEGER id PK
        TEXT username UK
        TEXT email UK
        TEXT hashed_password
        TEXT created_at
    }

    journal_entries {
        INTEGER id PK
        INTEGER user_id FK
        TEXT date
        TEXT entry_type
        TEXT artwork_title
        TEXT artwork_artist
        TEXT artwork_year
        TEXT essay_title
        TEXT essay_body
        TEXT questions
        TEXT comfort
        TEXT reflection
        TEXT moods
        TEXT dominant_colors
        TEXT thumbnail
        TEXT pre_emotions
        TEXT post_emotions
        TEXT mood_color
        TEXT mood_color_name
        TEXT mood_note
        TEXT sketch_image
        TEXT sketch_title
        TEXT sketch_note
        TEXT sketch_guide
        TEXT sketch_reflection
        TEXT ticket_memo
        TEXT ticket_exhibition
        TEXT era_data
        TEXT question_answers
        TEXT created_at
    }

    artists {
        INTEGER id PK
        TEXT name
        TEXT name_ko
        TEXT nationality
        TEXT years
        TEXT genre
        TEXT bio
        TEXT wikipedia
        INTEGER painting_count
        TEXT created_at
    }

    artworks {
        INTEGER id PK
        TEXT title
        TEXT title_ko
        INTEGER artist_id FK
        TEXT year
        TEXT medium
        TEXT museum
        TEXT genre
        TEXT description
        TEXT created_at
    }

    artist_quotes {
        INTEGER id PK
        TEXT quote
        TEXT quote_en
        TEXT artist
        TEXT artist_en
    }

    password_reset_tokens {
        INTEGER id PK
        INTEGER user_id FK
        TEXT token UK
        TEXT expires_at
        INTEGER used
        TEXT created_at
    }

    users ||--o{ journal_entries : writes
    users ||--o{ password_reset_tokens : requests
    artists ||--o{ artworks : painted
```

---

## Getting Started

### Requirements

- Python 3.11+
- Node.js 18+
- Gemini API Key
- Optional: Google Cloud Vision API Key, Roboflow API Key, KCISA API Key

### Environment Variables

```env
# Required
GEMINI_API_KEY=your-gemini-key
SECRET_KEY=your-jwt-secret

# Optional — PostgreSQL 사용 시. 미설정 시 SQLite 사용
DATABASE_URL=postgresql://user:password@host:port/dbname

# Optional
GOOGLE_CLOUD_VISION_KEY=your-key
ROBOFLOW_API_KEY=your-key
KCISA_API_KEY=your-key
```

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Docker (Recommended for Deployment)

```bash
docker build -t inner-gallery .
docker run -p 7860:7860 \
  -e GEMINI_API_KEY=your-key \
  -e SECRET_KEY=your-jwt-secret \
  inner-gallery
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

### Optional: Build FAISS Index

```bash
# Place Kaggle artwork datasets under backend/artwork_sources/
python backend/scripts/build_index.py
```

---

## Project Structure

```text
inner-gallery/
├── backend/
│   ├── main.py                 # API endpoints and analysis pipeline
│   ├── auth.py                 # JWT authentication, login, register, reset
│   ├── database.py             # SQLite / PostgreSQL CRUD auto-switch
│   ├── artwork_index/
│   │   ├── index.faiss         # CLIP ViT-B/32 vector index
│   │   └── metadata.json       # artwork metadata linked to FAISS index
│   ├── data/
│   │   └── artwork_era_db.json # curated art history context DB
│   └── scripts/                # dataset and DB pipeline scripts
│
├── modules/
│   ├── color_analyzer.py       # LAB KMeans color extraction, mood tagging
│   ├── composition_analyzer.py # composition, negative space, symmetry
│   ├── person_analyzer.py      # HOG + fallback person and posture analysis
│   ├── emotion_scorer.py       # 8D emotion vector calculation
│   ├── llm_generator.py        # docent essays, chat, era, sketch reflection
│   ├── artwork_matcher.py      # CLIP ViT-B/32 + FAISS matching pipeline
│   ├── era_lookup.py           # artwork_era_db.json lookup
│   ├── quality_checker.py      # camera-mode quality pre-check
│   ├── saliency_analyzer.py    # OpenCV saliency map generation
│   └── ocr_extractor.py        # artwork label OCR extraction
│
├── frontend/src/
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Upload.jsx
│   │   ├── Results.jsx
│   │   ├── Routine.jsx
│   │   ├── Drawing.jsx
│   │   ├── Journal.jsx
│   │   ├── JournalDetail.jsx
│   │   ├── Login.jsx
│   │   └── ResetPassword.jsx
│   ├── components/
│   ├── context/
│   └── utils/
│
├── Dockerfile
├── generate_icons.py
└── requirements.txt
```

---

## Engineering Challenges

| Challenge | Solution |
|---|---|
| 전시장 사진은 기울어짐, 반사광, 흐림, 프레임 누락이 자주 발생함 | 카메라 모드 전용 quality check, Roboflow frame detection, OpenCV perspective warp, fallback crop 적용 |
| 단일 이미지 인식 모델은 오탐 가능성이 큼 | CLIP/FAISS, Gemini Vision, Google Web Detection, OCR 힌트를 조합한 4-Way validation 설계 |
| LLM이 보이지 않는 표정이나 배경을 상상할 수 있음 | `safe_visual_facts`와 `blocked_uncertain_facts`를 분리하고 unsupported claim 검증 로직 추가 |
| 감정 해석이 단순 색상 매핑으로 보일 수 있음 | 색채, 구도, 여백, 대칭성, saliency, 인물 정보를 조합한 8D emotion vector 설계 |
| 감상 서비스가 치료·진단으로 오해될 수 있음 | 의료적 효능 표현 금지, 자기 회고 중심 UX, 완곡한 표현 정책 적용 |
| 티켓 이미지 저장 시 외부 이미지 CORS 문제가 발생할 수 있음 | 저장 전 외부 이미지를 data URL로 변환해 `html-to-image` 렌더링 안정화 |
| Hugging Face Spaces 환경에서 데이터 영구성이 제한될 수 있음 | SQLite 기본값 + `DATABASE_URL` 설정 시 Supabase PostgreSQL 자동 전환 구조 구현 |

---

## Future Improvements

- 실제 갤러리 촬영 데이터 기반 frame detection fine-tuning
- 한글 OCR 기반 작품 라벨 인식 고도화
- 저널 검색, 날짜 필터, 감정 태그 필터링 기능
- 사용자별 감상 패턴 분석 리포트
- 다국어 도슨트 해설 지원
- 작품 인식 실패 케이스 기반 active learning 데이터셋 구축
- 스케치 히스토리 및 시리즈 기록 기능
- 감상 통계 시각화: 캘린더 히트맵, 감정 분포 차트

---

## References & Licenses

### External APIs

| Service | Usage |
|---|---|
| **Google Gemini API** | 작품 멀티모달 식별, 도슨트 에세이 생성, 스케치 회고, 번역, 도슨트 채팅 |
| **Google Cloud Vision API** | Web Detection 기반 작품 교차 검증 |
| **Roboflow Serverless Workflows API** | 회화 경계 감지 및 작품 영역 자동 크롭 |
| **Art Institute of Chicago Public API** | 오늘의 명화 퍼블릭 도메인 작품 데이터 및 IIIF 이미지 제공 |
| **KCISA API** | 국내 공공 미술관·문화 기관 전시 정보 제공 |
| **Supabase** | PostgreSQL 기반 사용자 데이터 영구 저장 |

### Datasets & Models

| Resource | Usage |
|---|---|
| **Best Artworks of All Time** | CLIP/FAISS 인덱스 구축용 명화 이미지 데이터 |
| **Greatest of All Time Painters** | FAISS 인덱스 확장용 작품 이미지 |
| **AIC Public Domain Collection** | 오늘의 명화 큐레이션 |
| **CLIP ViT-B/32** | 작품 이미지 임베딩 생성 |
| **OpenCV models** | Saliency, Haar Cascade 등 시각 분석 fallback |

### License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
