---
title: Inner Gallery Api
emoji: 🖼️
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: An AI-powered art journal using computer vision and LLM
---

<br />
<img width="2123" height="724" alt="헤더이미지" src="https://github.com/user-attachments/assets/c1d664e8-10f2-4183-a0de-f9f486f2cb30" />

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
[![PostgreSQL](https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=flat-square&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/License-MIT-C9A84C?style=flat-square)](LICENSE)

<br />

**명화를 인식하고 설명하는 것을 넘어, 작품의 색·구도·여백을 사용자의 감정 회고와 연결하는 AI 기반 아트 저널 서비스**

</div>

---

## Table of Contents

- [Overview](#overview)
- [Why I Built This](#why-i-built-this)
- [What I Built](#what-i-built)
- [Experience Flow](#experience-flow)
- [Core Features](#core-features)
- [Safety & Grounding](#safety--grounding)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Overview](#api-overview)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [Feature Flow](#feature-flow)
- [References & External Resources](#references--external-resources)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Overview

**Inner Gallery**는 명화를 단순히 인식하고 해설하는 AI 앱이 아니라, 작품을 매개로 사용자가 오늘의 마음을 돌아보고 기록할 수 있도록 설계한 **아트테라피 영감 기반 AI 아트 저널**입니다.

사용자가 작품 이미지를 촬영하거나 업로드하면 시스템은 먼저 작품 프레임을 감지하고 원근을 보정합니다. 이후 CLIP+FAISS, Gemini Vision, Google Web Detection, OCR 힌트 기반 식별을 조합해 작품 후보를 검증하고, 색채·구도·여백·인물 요소를 컴퓨터 비전으로 분석합니다.

그 결과를 바탕으로 사용자의 현재 감정과 연결된 **맞춤형 감상 해설**, **마음색**, **스케치 회고**, **전시 티켓 형태의 감상 기록**을 생성합니다. 또한 Art Institute of Chicago Public API를 통해 매일 새로운 퍼블릭 도메인 명화를 큐레이션하고, 전국 미술관·갤러리 전시 정보를 통합 제공합니다.

> Inner Gallery는 작품을 설명하는 AI가 아니라,  
> **작품을 통해 나를 돌아보게 하는 AI**입니다.

본 프로젝트는 의료적 치료나 심리 진단을 제공하지 않습니다. 다만 아트테라피의 감상 방식에서 영감을 받아, 작품의 시각 요소를 통해 감정을 언어화하고 개인적인 기록으로 남기는 경험을 제공합니다.

---

## Why I Built This

미술 감상은 흔히 작품명, 작가, 사조, 역사적 배경을 이해하는 **지식 중심 경험**으로 소비됩니다. 하지만 실제로 그림 앞에 오래 머무르게 되는 순간은 반드시 정보에서만 오지 않습니다.

어떤 작품은 색 하나로 마음을 누그러뜨리고, 어떤 구도는 말로 설명하기 어려운 고요함을 만들며, 어떤 여백은 오늘의 감정을 다시 바라보게 합니다.

**Inner Gallery**는 이 감상 경험을 기술적으로 구현해보고자 시작한 프로젝트입니다. 단순히 명화를 맞히고 설명하는 데 그치지 않고, 작품의 색채와 구도, 여백, 시선 흐름이 사람의 정서에 어떻게 닿을 수 있는지를 컴퓨터 비전으로 분석하고, 이를 사용자의 현재 감정과 연결해 개인적인 회고 경험으로 확장하는 것을 목표로 했습니다.

이 과정에서 가장 중요하게 본 것은 두 가지입니다.

1. **감상문이 근거 없는 감성문으로 흐르지 않도록 만들 것**  
   실제 시각 분석 결과와 검증된 작품 정보를 기반으로 AI 해설을 생성하도록 설계했습니다.

2. **감상 이후의 마음 변화가 사라지지 않도록 기록화할 것**  
   작품 정보, 감정, 질문, 스케치, 회고를 하나의 전시 티켓처럼 저장해 개인적인 아카이브로 남길 수 있게 했습니다.

즉, Inner Gallery는 작품을 평가하거나 단순히 설명하는 앱이 아니라, **작품을 매개로 자신의 감정을 언어화하고 기록하는 AI 기반 아트 저널**입니다.

---

## What I Built

이 프로젝트는 외부 API 호출만으로 구성된 단순 데모가 아니라, **명화 감상이라는 도메인에 맞춘 데이터 자산, 컴퓨터 비전 파이프라인, LLM 안전장치, 저널 UX**를 직접 설계한 풀스택 AI 서비스입니다.

### 직접 구축한 데이터 자산

| Asset | Description |
|---|---|
| `artwork_era_db.json` | 6,905줄 규모의 명화 맥락 지식 DB. 작품별 사조, 제작 배경, 시대 맥락, 작가 생애, 시각적 연결 정보를 직접 큐레이션 |
| `index.faiss` | 18,455개 명화 이미지를 CLIP ViT-B/32로 임베딩한 로컬 벡터 검색 인덱스 |
| `metadata.json` | FAISS 검색 결과와 연결되는 작품명, 작가, 장르, 연도 등 메타데이터 |
| `artist_quotes` | 세계 주요 예술가 120+명의 명언 데이터. 한국어·영문 병행 수록 |
| `database` | 사용자, 감상 기록, 스케치, 감정 태그, 명언을 저장하는 SQLite / Supabase PostgreSQL |
| `backend/scripts/` | 데이터셋 전처리, FAISS 인덱스 빌드, 작가 정보 임포트, DB 검증 및 마이그레이션 스크립트 |

### 직접 설계한 CV/AI 파이프라인

- Roboflow 기반 작품 프레임 감지 및 8% padding crop
- OpenCV 기반 Perspective Warp로 비스듬한 작품 사진 정면 보정
- Laplacian variance, brightness, glare ratio, artwork size 기반 화질 사전 검사 (카메라 모드 전용)
- CLIP ViT-B/32 + FAISS IndexFlatIP 기반 로컬 벡터 검색 (top-k=12, threshold=0.78, vote_min=2)
- Gemini Vision, Google Web Detection, OCR 힌트를 조합한 4-Way 작품 식별
- CIE LAB 색공간 KMeans(k=5) 기반 주조색 추출 및 명화 도메인 특화 색채 분석
- 구도, 여백, 대칭성, 주목도(Saliency Map) 분석
- HOG, Haar Cascade, 피부색 fallback을 조합한 미술 작품 인물 감지
- `safe_visual_facts` / `blocked_uncertain_facts` 분리로 LLM 환각 방지
- 생성 후 unsupported visual claim 검증 및 재생성 파이프라인

### 기획·UX 설계 포인트

- 작품 해설을 "정답 제공"이 아니라 "자기 회고"로 이어지게 하는 3단계 감상 구조 설계
- 감상 전/후 감정 키워드 선택으로 감상 경험 변화 추적 (27개 감정 카테고리, 6개 그룹)
- 감상 후 스케치를 남기고 AI 회고문으로 다시 해석하는 Mind Sketch UX 구현
- HSL 색공간 기반 마음색 직접 선택 (HUE·SATURATION·LIGHTNESS 슬라이더)
- Art Institute of Chicago Public Domain API 연동 일일 명화 큐레이션
- 국립현대미술관, 예술의전당 등 국내 27개 기관 + AIC 전시 정보 통합 제공
- 감상 기록을 전시 티켓 형태(No. IG-YYMMDD)로 저장하고 이미지로 저장·공유하는 Journal UX
- PWA(Progressive Web App) 지원으로 홈 화면 설치 가능
- 의료적 치료·진단처럼 보이지 않도록 표현 범위와 안전 문구를 명확히 제한

---

## Experience Flow

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
사용자 감정 상태 입력 (전 감정 키워드 선택)
        ↓
AI 도슨트 해설 생성 + 감상 질문 + 마음색 제안
        ↓
도슨트 채팅 / 감상 질문 답변 / 사조·시대 맥락 조회
        ↓
마음 스케치 → Gemini AI 회고문 생성
        ↓
감상 후 감정 키워드 선택 (후 감정)
        ↓
전시 티켓 형태로 저장 → Inner Gallery 아카이브
        ↓
[별도] 오늘의 명화 / 전시 정보 / 예술가 명언 큐레이션
```

```mermaid
flowchart TD
    A[Artwork Image Upload / Camera] --> B{Camera Mode?}
    B -->|Yes| C[Quality Check: Blur / Glare / Brightness]
    B -->|No| D[Artwork Frame Detection & Perspective Warp]
    C --> D
    D --> E[Hybrid Artwork Recognition]
    E --> E1[CLIP ViT-B/32 + FAISS]
    E --> E2[Gemini 2.0 Flash Vision]
    E --> E3[Google Web Detection]
    E --> E4[OCR Hint Injection]
    E --> F[CV Analysis Pipeline]
    F --> F1[LAB KMeans Color]
    F --> F2[Composition & Saliency]
    F --> F3[Person & Posture]
    F --> G[8D Emotion Vector]
    G --> H[Grounded AI Docent + Reflection Questions]
    H --> I[Docent Chat]
    H --> J[Mind Sketch]
    J --> K[Gemini Sketch Reflection]
    K --> L[Journal Ticket Archive]

    M[Daily Artwork AIC API] --> N[Reflection Q&A]
    N --> L
```

---

## Core Features

### 1. Artwork Recognition — 4-Way Hybrid Validation

단일 모델에 의존하지 않고 네 가지 인식 경로를 교차 검증합니다.

| Engine | Role |
|---|---|
| **CLIP ViT-B/32 + FAISS** | 18,455개 명화 이미지 로컬 벡터 인덱스. L2 정규화 후 IndexFlatIP로 코사인 유사도 검색. top-k=12, threshold=0.78, vote_min=2 다중 투표 방식으로 오탐 최소화 |
| **Gemini 2.0 Flash Vision** | 작품명·작가·연도 후보 추출, 이미지 내 OCR, 인물 표정·자세 동시 분석 |
| **Google Cloud Vision Web Detection** | 미술관·위키피디아 등 신뢰 도메인 기반 웹 교차 검증, best_guess 및 엔티티 추출 |
| **OCR Hint Injection** | 전시장 작품 라벨의 제목·작가 정보를 추출해 인식 힌트로 사용. 신뢰도 평가 후 strong / partial / rejected 분류 |

식별 결과는 다음 상태로 분류합니다.

| Status | Meaning |
|---|---|
| `confirmed` | 내부 인덱스와 외부 검증 결과가 모두 높은 신뢰도로 일치 |
| `internal_match` | 로컬 FAISS 기반 유사도는 높지만 외부 검증은 제한적 |
| `web_confirmed` | 웹 검증 결과가 강하게 일치 |
| `unknown` | 작품명을 단정하지 않고 색채·구도 중심 감상으로 전환 |

불확실한 작품은 억지로 추정하지 않고, **식별 가능한 시각 요소 중심의 감상 경험**으로 자연스럽게 전환합니다.

---

### 2. Computer Vision Pipeline

LLM에 이미지를 바로 넘기지 않고, 먼저 컴퓨터 비전 파이프라인을 통해 해설의 근거가 되는 시각 정보를 추출합니다.

#### Input Quality Check (카메라 모드 전용)

| Check | Algorithm | Threshold |
|---|---|---|
| Blur | Laplacian variance | `< 75.0` |
| Darkness | Average brightness | `< 0.12` |
| Glare | Bright pixel ratio + largest blob | `> 8%` or blob `> 1.5%` |
| Artwork size | bbox / image area | `< 15%` |

이미지 업로드 모드에서는 화질 경고를 표시하지 않습니다. 사용자가 직접 선택한 이미지에 대해 불필요한 경고를 줄이기 위한 의도적 설계입니다.

#### Frame Detection & Perspective Warp

```python
# Dynamic Canny threshold
v = np.median(blur)
edges = cv2.Canny(blur, lower=0.67 * v, upper=1.33 * v)

# Convex quadrilateral detection → Homography
M = cv2.getPerspectiveTransform(src_corners, dst_corners)
warped = cv2.warpPerspective(img, M, (target_w, target_h))
```

사각형 윤곽 검출에 실패하면 8% padding crop으로 fallback합니다. 원본과 crop 이미지를 함께 분석하는 dual-image 전략으로 인식 안정성을 높였습니다.

#### Color, Composition, Saliency

| Area | Implementation |
|---|---|
| **Color** | CIE LAB 색공간에서 KMeans(k=5)로 주조색 5가지 추출, RGB/HSV/점유율 계산 |
| **Custom Color Rules** | 무채색 필터, Gold/Amber 별도 분류, 밝은 영역 위치 추적 |
| **Composition** | 9분할 위치, 여백 비율, 대칭성, 피사체 규모, edge direction 분석 |
| **Saliency** | OpenCV StaticSaliencySpectralResidual + 대비 기반 fallback |

---

### 3. Emotion Map — 8차원 감정 벡터

색채·구도·인물 분석값을 조합해 8가지 감정 차원을 계산하고, 사용자 선택 감정 키워드와 교차 반영합니다.

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

### 4. Emotion Keyword Selection

사용자가 감상 전·후 감정 상태를 직접 선택해 AI 해설 생성에 반영합니다.

**감정 카테고리 (6그룹, 45종)**

| 그룹 | 키워드 예시 |
|---|---|
| 가라앉음 | 슬픔, 외로움, 그리움, 공허함, 상처, 자괴감, 후회, 자책, 절망, 무기력 |
| 불안과 흔들림 | 불안, 긴장감, 두려움, 막연함, 내적 갈등 |
| 분노와 복잡한 감정 | 짜증, 화, 증오, 애증 |
| 안정과 위로 | 평온함, 편안함, 여유, 온기, 위로, 수용, 화해 |
| 회복과 긍정 | 회복, 희망, 기쁨, 설렘, 자신감, 열정, 자유로움, 영감 |
| 깊은 감각과 바라봄 | 감동, 경이로움, 성찰, 집중, 깨달음, 배려심, 통찰 |

감상 전(pre_emotions)과 감상 후(post_emotions)를 별도로 기록해 작품 경험 전후의 감정 변화를 추적합니다.

---

### 5. Grounded AI Docent

AI 도슨트는 다음 데이터를 기반으로 해설을 생성합니다.

- `safe_visual_facts`: 신뢰도 높은 시각 분석 결과
- `blocked_uncertain_facts`: 추측이 금지된 불확실한 항목
- 직접 구축한 작품 맥락 DB (`artwork_era_db.json`)
- 8차원 감정 벡터 및 사용자 감정 상태
- 사용자가 선택한 해설 스타일 및 분석 포커스

해설은 항상 다음 3단계 구조를 따릅니다.

```text
1. 시각 분석    색채·구도·여백·인물 요소 묘사
2. 정서적 작용  시각 요소가 감상자에게 줄 수 있는 감각 설명
3. 자기 회고   작품을 통해 자신의 마음을 돌아보는 질문 제안
```

지원하는 해설 스타일은 `아트 테라피`, `도슨트 해설`, `시각 분석`, `짧은 감상`입니다.

#### Docent Chat

작품 분석 결과를 컨텍스트로 도슨트와 실시간 대화할 수 있습니다. 작품 정보, 색채 분석, 감정 지도, 사용자 감정 상태를 모두 프롬프트에 주입해 맥락 있는 대화를 지원합니다.

#### Era & Art Movement Lookup

작품 식별이 확정되면 직접 구축한 `artwork_era_db.json`에서 해당 작품의 사조, 제작 시대, 역사적 맥락, 작가 생애, 시각적 연결 정보를 즉시 조회합니다. DB에 없는 경우 Gemini로 생성 후 반환합니다.

---

### 6. Daily Curation — 오늘의 아트 큐레이션

#### 오늘의 명화

Art Institute of Chicago Public Domain Collection API를 통해 매일 다른 퍼블릭 도메인 명화를 제공합니다.

- 4,000개 이상의 퍼블릭 도메인 작품 풀에서 날짜 기반 결정론적 선택
- AIC IIIF Image API를 통한 고화질 이미지 제공
- 작품 설명 한국어 번역 (Gemini 기반)
- 매일 30개의 감상 질문 중 무작위 선택 제시
- "다른 작품 보기"로 랜덤 전환 가능 (로드 완료 전 재클릭 방지)
- 감상 질문 답변 작성 후 저널에 저장

#### 오늘의 전시 산책

국내외 미술 기관 전시 정보를 통합 제공합니다.

| 소스 | 내용 |
|---|---|
| 국립현대미술관 KCISA API | 현재 전시 정보 (국립 기관 27개 포함) |
| 예술의전당 API | 현재 진행 전시 |
| Art Institute of Chicago | AIC 현재 전시 (영문, `Confirmed` 상태 필터링) |

#### 예술가의 한 문장

세계 주요 예술가 120+명의 명언을 한국어·영문 병행 표시합니다. 레오나르도 다 빈치, 반 고흐, 피카소, 모네, 클림트 등 20명 이상의 화가 명언을 직접 큐레이션했습니다.

---

### 7. Mind Sketch & Mood Color

#### Mind Sketch

감상 후 HTML5 Canvas에 마음의 흔적을 남길 수 있습니다.

| Mode | Description |
|---|---|
| 선으로 남기기 | 감정의 방향을 선과 형태로 표현 |
| 색으로 채우기 | 감정에 가까운 색으로 캔버스를 채움 |
| 문장 쓰기 | 작품이 건넨 말을 짧게 기록 |

- 실행 취소(Undo) / 전체 지우기 지원
- 작품 이미지를 배경 오버레이로 사용 가능
- Gemini Vision이 선·색·여백을 읽어 2~3문장 또는 4항목 심층 회고문 생성

#### Mood Color — 마음색

감상 후 오늘의 감정을 색으로 표현합니다.

- **팔레트 선택**: 분석된 작품 색상 팔레트에서 선택
- **감정-색 매핑**: 평온함(청록), 따뜻함(베이지), 우울함(남색) 등 30종 감정-색 사전 매핑
- **직접 고르기**: HUE·SATURATION·LIGHTNESS 슬라이더로 세밀한 색 조정 (터치 드래그 최적화)
- 선택한 마음색과 이름은 저널에 함께 저장

---

### 8. Art Journal — 전시 티켓 아카이브

모든 감상 경험은 **전시 티켓(No. IG-YYMMDD-XXXX)** 형태로 저장됩니다.

#### 저장되는 정보

| Field | Content |
|---|---|
| 작품 정보 | 제목, 작가, 제작 연도 |
| AI 해설 | 에세이 본문, 감상 질문, 위로 메시지 |
| 감정 데이터 | 감상 전·후 감정 키워드, 마음색, 무드 태그 |
| 사용자 기록 | 직접 작성한 감상 후기, 질문 답변, 전시 메모 |
| 스케치 | 마음 스케치 이미지, 스케치 제목, 회고문 |
| 시대 정보 | 작품 사조, 역사적 맥락, 작가 생애 |
| 썸네일 | 작품 썸네일 이미지 (480×360 JPEG) |

#### 티켓 기능

- **이미지 저장**: `html-to-image` 기반으로 티켓 전체를 PNG로 저장. 외부 이미지 CORS 문제를 사전 data URL 변환으로 해결
- **공유하기**: Web Share API 지원 기기에서 직접 공유, 미지원 시 이미지 다운로드 fallback
- **전시 장소 수정**: 티켓 내 전시 제목/장소를 직접 편집 가능
- **메모 편집**: 티켓 하단 개인 메모 인라인 편집

#### 인증 시스템

- JWT 기반 인증 (30일 만료)
- 비밀번호 재설정 (이메일 + 새 비밀번호 방식)
- `SECRET_KEY` 환경변수 고정으로 서버 재시작 후에도 기존 토큰 유지

---

## Safety & Grounding

Inner Gallery는 LLM의 감성적 글쓰기가 근거 없는 해설로 흐르지 않도록 다음 장치를 둡니다.

- 불확실한 표정·시선·자세는 `blocked_uncertain_facts`로 분리해 LLM 프롬프트에서 제외
- 추상화·풍경·정물·건축 작품에서는 인물 분석 자동 비활성화
- 의료적 치료, 심리 진단, 정서 개선 효과 표현 금지
- 감상자의 현재 감정을 단정하지 않고 `~처럼 느껴질 수 있어요`, `~일지도 모릅니다` 표현 사용
- 작품 식별 신뢰도가 낮을 경우 작품명 단정을 피하고 시각 분석 중심 감상으로 전환
- 생성 후 근거 없는 시각 주장(`unsupported_visual_claims`) 검증 및 필요 시 재생성

---

## Tech Stack

| Area | Stack |
|---|---|
| **Frontend** | React 18, Vite, React Router v6, HTML5 Canvas, Vanilla CSS, Axios |
| **PWA** | Web App Manifest, Service Worker ready, apple-touch-icon, theme-color |
| **Backend** | Python 3.11, FastAPI, Uvicorn, JWT (python-jose), bcrypt |
| **Database** | SQLite (로컬/HF Spaces) / Supabase PostgreSQL (`DATABASE_URL` 환경변수로 자동 전환) |
| **Computer Vision** | OpenCV, Roboflow Serverless, KMeans, HOG, Haar Cascade, Saliency Map, Perspective Transform |
| **AI / ML** | Gemini 2.0 Flash, Google Cloud Vision API, CLIP ViT-B/32, FAISS IndexFlatIP, scikit-learn, NumPy |
| **External APIs** | Art Institute of Chicago Public API (IIIF), 국립문화정보원 KCISA API |
| **Deployment** | Docker, HuggingFace Spaces (port 7860) |
| **Data** | `artwork_era_db.json`, `index.faiss`, `metadata.json`, artist_quotes (DB seeded) |

---

## Getting Started

### Requirements

- Python 3.11+
- Node.js 18+
- Gemini API Key
- Optional: Google Cloud Vision API Key, Roboflow API Key

### Environment Variables

```env
# Required
GEMINI_API_KEY=your-gemini-key
SECRET_KEY=your-jwt-secret          # JWT 시크릿, 미설정 시 재시작마다 재생성

# Optional — PostgreSQL 사용 시 (미설정 시 SQLite)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Optional
GOOGLE_CLOUD_VISION_KEY=your-key
ROBOFLOW_API_KEY=your-key
KCISA_API_KEY=your-key              # 국내 전시 정보 API
```

> **PostgreSQL (Supabase) 설정**: `DATABASE_URL` 환경변수를 설정하면 SQLite 대신 Supabase PostgreSQL을 자동으로 사용합니다. HuggingFace Spaces에서 데이터를 영구 보존하려면 Supabase 연결을 권장합니다.

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
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
│   ├── database.py             # SQLite / PostgreSQL CRUD (auto-switch)
│   ├── artwork_index/
│   │   ├── index.faiss         # CLIP ViT-B/32 vector index (18,455 artworks)
│   │   └── metadata.json       # artwork metadata linked to FAISS index
│   ├── data/
│   │   └── artwork_era_db.json # curated art history context DB (6,905 lines)
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
│   ├── quality_checker.py      # image quality pre-check (camera mode)
│   ├── saliency_analyzer.py    # OpenCV saliency map generation
│   └── ocr_extractor.py        # artwork label OCR extraction
│
├── frontend/src/
│   ├── pages/
│   │   ├── Home.jsx            # main menu + AI pipeline explainer
│   │   ├── Upload.jsx          # image upload / camera capture + pre-analysis
│   │   ├── Results.jsx         # full analysis results + docent + journal save
│   │   ├── Routine.jsx         # daily artwork / exhibitions / artist quotes
│   │   ├── Drawing.jsx         # HTML5 Canvas mind sketch
│   │   ├── Journal.jsx         # ticket-style journal list + image export
│   │   ├── JournalDetail.jsx   # full journal entry view
│   │   ├── Login.jsx           # login / register / password reset
│   │   └── ResetPassword.jsx   # standalone password reset page
│   ├── components/             # GoldDivider, EmotionBar, PaletteBar, LoginModal
│   ├── context/                # AppContext (global state), AuthContext (JWT)
│   └── utils/                  # artwork detection, fuzzy match helpers
│
├── Dockerfile                  # multi-stage build: Python deps → npm build → uvicorn
├── generate_icons.py           # PWA icon generation from embedded base64
└── requirements.txt
```

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | 이미지 전체 분석 파이프라인 실행 (CV + 4-Way 식별 + 해설 생성) |
| `POST` | `/api/quick-match` | 업로드 즉시 Top-5 작품 후보 미리보기 (CLIP + FAISS) |
| `POST` | `/api/quick-quality` | 이미지 화질 사전 검사 (카메라 모드 전용) |
| `POST` | `/api/sketch-reflection` | 마음 스케치 이미지 기반 AI 회고문 생성 (Gemini Vision) |
| `POST` | `/api/essay-text` | 작품 정보 기반 도슨트 에세이 텍스트 재생성 |
| `POST` | `/api/artwork-era` | 작품 사조·시대·작가 맥락 조회 (DB lookup → Gemini fallback) |
| `POST` | `/api/docent-chat` | 작품 컨텍스트 기반 도슨트 실시간 채팅 |
| `POST` | `/api/translate` | 영어 작품 설명 한국어 번역 (Gemini) |
| `GET` | `/api/daily-artwork` | 서버 사이드 오늘의 명화 추천 |
| `GET` | `/api/artist-quote` | 예술가 명언 랜덤 반환 |
| `GET` | `/api/exhibitions` | 국내외 전시 정보 (KCISA + AIC 통합) |
| `GET` | `/api/demo-result` | 작품 분석 데모 결과 반환 |
| `GET` | `/api/journal` | 감상 기록 목록 조회 |
| `POST` | `/api/journal/thumbs` | 날짜 목록 기반 썸네일 배치 조회 |
| `GET` | `/api/journal/detail/{date}` | 감상 기록 상세 조회 |
| `POST` | `/api/journal` | 감상 기록 저장 |
| `DELETE` | `/api/journal/{date}` | 감상 기록 삭제 |
| `PATCH` | `/api/journal/{date}/note` | 티켓 메모 수정 |
| `PATCH` | `/api/journal/{date}/exhibition` | 티켓 전시 제목 수정 |
| `PATCH` | `/api/journal/{date}/sketch` | 마음 스케치 데이터 업데이트 |
| `POST` | `/api/auth/register` | 회원가입 |
| `POST` | `/api/auth/login` | 로그인 (JWT 발급) |
| `GET` | `/api/auth/me` | 현재 사용자 정보 |
| `DELETE` | `/api/auth/me` | 계정 탈퇴 (저널 데이터 포함 삭제) |
| `POST` | `/api/auth/reset-password` | 비밀번호 재설정 |

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Browser / PWA)                      │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │  Upload  │  │ Results  │  │ Journal  │  │  Routine / Drawing   │ │
│  │  Camera  │  │ (Detail) │  │ (Ticket) │  │  (Daily / Sketch)    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘ │
│       │              │              │                    │             │
│       └──────────────┴──────────────┴────────────────────┘            │
│                               Axios (JWT Bearer)                      │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │ HTTPS
                          ┌─────────▼──────────┐
                          │    FastAPI (Python) │
                          │    Uvicorn / Docker │
                          │       port 7860     │
                          └─────────┬──────────┘
               ┌─────────────────────────────────────────┐
               │                                         │
    ┌──────────▼──────────┐               ┌─────────────▼──────────────┐
    │   CV / AI Pipeline  │               │        Database Layer       │
    │                     │               │                             │
    │  ┌───────────────┐  │               │  SQLite  ──or──  Supabase  │
    │  │ Roboflow API  │  │               │      PostgreSQL             │
    │  │ (frame crop)  │  │               │                             │
    │  ├───────────────┤  │               │  users                      │
    │  │ OpenCV        │  │               │  journal_entries            │
    │  │ Color/Comp/   │  │               │  artists                    │
    │  │ Person/Sal    │  │               │  artworks                   │
    │  ├───────────────┤  │               │  artist_quotes              │
    │  │ CLIP ViT-B/32 │  │               │  password_reset_tokens      │
    │  │ + FAISS Index │  │               └─────────────────────────────┘
    │  ├───────────────┤  │
    │  │ Gemini 2.0    │  │          ┌─────────────────────────────────┐
    │  │ Flash Vision  │  │          │         Static Assets           │
    │  ├───────────────┤  │          │                                 │
    │  │ Google Cloud  │  │          │  frontend/dist/  ←  Vite build  │
    │  │ Vision API    │  │          │  (React SPA + manifest + icons) │
    │  └───────────────┘  │          └─────────────────────────────────┘
    └─────────────────────┘
```

### CV + AI Analysis Pipeline

```mermaid
flowchart LR
    A[Raw Image] --> B[Roboflow\nPainting Detection]
    B -->|bbox + 8% padding| C[Cropped ROI]
    B -->|detection failed| C2[Client-side\nSobel Crop]
    C2 --> C

    C --> D1[OpenCV\nLAB KMeans\nColor Analysis]
    C --> D2[OpenCV\nComposition\n& Saliency]
    C --> D3[OpenCV\nHOG + Haar\nPerson Analysis]
    C --> D4[CLIP ViT-B/32\n→ 512-dim emb\nFAISS Search]
    C --> D5[Gemini 2.0 Flash\nVision + OCR]
    C --> D6[Google Cloud\nVision\nWeb Detection]

    D4 -->|sim≥0.78\nvote≥2| E[FAISS Match]
    D5 --> E2[Gemini\nCandidates]
    D6 --> E3[Web Entities\n& Best Guess]

    E --> F{4-Way\nCross Validation}
    E2 --> F
    E3 --> F

    D1 --> G[8D Emotion\nVector]
    D2 --> G
    D3 --> G

    F -->|confirmed / unknown| H[Artwork Identity\n+ era_db Lookup]
    G --> I[Grounded\nDocent Essay\nGemini 2.0 Flash]
    H --> I
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as Database

    C->>API: POST /api/auth/register {username, email, password}
    API->>API: bcrypt.hashpw(password)
    API->>DB: INSERT INTO users
    DB-->>API: ok
    API-->>C: {ok: true}

    C->>API: POST /api/auth/login {username, password}
    API->>DB: SELECT * FROM users WHERE username=?
    DB-->>API: user row
    API->>API: bcrypt.checkpw() → JWT encode(sub=user_id, exp=30d)
    API-->>C: {access_token, username, user_id}

    C->>API: POST /api/journal (Authorization: Bearer <token>)
    API->>API: jwt.decode() → user_id
    API->>DB: SELECT * FROM users WHERE id=?
    DB-->>API: user row
    API->>DB: INSERT INTO journal_entries
    API-->>C: {ok: true}
```

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

    users ||--o{ journal_entries : "writes"
    users ||--o{ password_reset_tokens : "requests"
    artists ||--o{ artworks : "painted"
```

**`journal_entries` 컬럼 타입 노트**

| 컬럼 | 실제 타입 | 직렬화 형식 |
|---|---|---|
| `essay_body`, `questions`, `moods`, `dominant_colors`, `pre_emotions`, `post_emotions` | JSON Array | `["item1", "item2"]` |
| `era_data` | JSON Object (또는 빈 문자열) | `{"art_movement": "...", ...}` |
| `question_answers` | JSON Object | `{"0": "답변 텍스트"}` |
| `thumbnail`, `sketch_image` | Base64 JPEG (또는 HTTP URL) | — |

---

## Feature Flow

### 작품 분석 → 저장 전체 흐름

```mermaid
flowchart TD
    A([이미지 업로드 / 카메라 촬영]) --> B{카메라 모드?}
    B -->|Yes| C[화질 검사\nBlur·Glare·Darkness]
    B -->|No| D[Client-side Sobel Crop]
    C -->|경고| D
    D --> E[POST /api/quick-match\nCLIP+FAISS Top-5 미리보기]
    E --> F[사용자: 힌트 입력 / 감정 선택 / 설정]
    F --> G[POST /api/analyze\n전체 분석 파이프라인]
    G --> H{식별 상태}
    H -->|confirmed| I[작품 정보 + era_db 조회]
    H -->|unknown| I2[색채·구도 중심 감상]
    I --> J[도슨트 에세이 생성\nGemini 2.0 Flash]
    I2 --> J
    J --> K[Results 페이지\n에세이·질문·마음색·감정바]
    K --> L{저장?}
    L -->|Yes| M[감상 후 감정 선택]
    M --> N[POST /api/journal\n전시 티켓 저장]
    N --> O([Journal 아카이브])
    K --> P[마음 스케치]
    P --> Q[POST /api/sketch-reflection\nGemini Vision 회고]
    Q --> N
```

### 오늘의 명화 흐름

```mermaid
flowchart TD
    A([Routine 페이지 진입]) --> B[getDailyArtworkAIC\n날짜 기반 결정론적 선택]
    B --> C[AIC Public API\n퍼블릭 도메인 작품 조회]
    C --> D[작품 이미지 + 메타데이터 표시\nAIC IIIF Image API]
    D --> E{번역 요청?}
    E -->|Yes| F[POST /api/translate\nGemini 한국어 번역]
    F --> D
    D --> G[오늘의 질문 표시\n30개 중 날짜 기반 선택]
    G --> H[사용자 답변 입력]
    H --> I[POST /api/journal\n감상 기록 저장]
    I --> J([Journal 아카이브])
    D --> K[다른 작품 보기\nRandom offset]
    K --> C
```

### 감상 기록 조회 흐름

```mermaid
flowchart TD
    A([Journal 페이지]) --> B[GET /api/journal\n텍스트 메타 + thumbnail 한번에 수신]
    B --> C[티켓 카드 목록 렌더링]
    C --> D{티켓 클릭}
    D --> E[GET /api/journal/detail/date\n전체 컬럼 수신]
    E --> F[JournalDetail 렌더\n에세이·질문·감정·스케치·시대정보 한번에 표시]
    F --> G{VIEW REPORT}
    G -->|펼치기| H[에세이 본문 + 질문·답변 + 시대 맥락]
    F --> I{티켓 이미지 저장/공유}
    I --> J[html-to-image → PNG\n외부 이미지 data URL 변환]
    J --> K([PNG 저장 / Web Share API])
```

---

## References & External Resources

이 프로젝트에서 사용한 외부 API, 오픈소스 모델, 데이터셋, 라이브러리를 모두 기록합니다.

---

### External APIs

| Service | Usage | License / Terms |
|---|---|---|
| **Google Gemini API** (Gemini 2.0 Flash) | 작품 멀티모달 식별, 도슨트 에세이 생성, 스케치 회고, 번역, 도슨트 채팅 | [Google AI Terms](https://ai.google.dev/terms) |
| **Google Cloud Vision API** | 웹 이미지 역검색(Web Detection)을 통한 작품 교차 검증 | [Google Cloud Terms](https://cloud.google.com/terms) |
| **Roboflow Serverless Workflows API** | 회화 경계 감지(Object Detection) 및 작품 영역 자동 크롭 | [Roboflow Terms](https://roboflow.com/terms) |
| **Art Institute of Chicago (AIC) Public API** | 오늘의 명화 퍼블릭 도메인 작품 데이터 및 IIIF 고화질 이미지 제공 | [AIC API Docs](https://api.artic.edu/docs/) · CC0 |
| **AIC IIIF Image API** | `/{image_id}/full/843,/0/default.jpg` 형식의 작품 원본 이미지 스트리밍 | CC0 Public Domain |
| **국립문화정보원 KCISA API** | 국내 공공 미술관·문화 기관 전시 정보 (국립현대미술관 외 27개 기관) | [공공데이터포털](https://www.data.go.kr/) |
| **Supabase** (선택) | PostgreSQL 기반 사용자 데이터 영구 저장 (DATABASE_URL 환경변수 설정 시) | [Supabase Terms](https://supabase.com/terms) |

---

### Datasets

| Dataset | Source | Usage |
|---|---|---|
| **Best Artworks of All Time** | [Kaggle — ikarus777](https://www.kaggle.com/datasets/ikarus777/best-artworks-of-all-time) | 50명 주요 화가 8,446점 이미지. CLIP 임베딩 인덱스 구축에 사용 |
| **Greatest of All Time (GOATs) Painters** | Kaggle | 추가 화가 작품 이미지. Best Artworks와 병합하여 FAISS 인덱스 확장 |
| **AIC Public Domain Collection** | [Art Institute of Chicago](https://www.artic.edu/open-access/open-access-images) | 퍼블릭 도메인 명화 4,000+점. 오늘의 명화 큐레이션에 실시간 활용. CC0 |

> FAISS 인덱스(`index.faiss`)는 위 Kaggle 데이터셋을 직접 다운로드 후 `backend/scripts/build_index.py`를 실행해 재현할 수 있습니다. 데이터셋 원본 이미지는 저장소에 포함되지 않습니다.

---

### Pre-trained Models

| Model | Source | Usage |
|---|---|---|
| **CLIP ViT-B/32** | [OpenAI CLIP](https://github.com/openai/CLIP) via [sentence-transformers](https://www.sbert.net/) (`clip-ViT-B-32`) | 작품 이미지 → 512차원 벡터 임베딩. 코사인 유사도 기반 FAISS 검색의 핵심 인코더 |
| **OpenCV StaticSaliencySpectralResidual** | [OpenCV](https://opencv.org/) (BSD License) | Spectral Residual 기법 기반 Saliency Map 생성. 작품 내 시선 집중 영역 감지 |
| **OpenCV Haar Cascade (haarcascade_frontalface_default)** | OpenCV 내장 모델 | 인물 분석 파이프라인의 얼굴 감지 fallback |

---

### Open Source Libraries

#### Backend (Python)

| Library | Version | License | Usage |
|---|---|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | ≥0.111 | MIT | REST API 서버 프레임워크 |
| [Uvicorn](https://www.uvicorn.org/) | ≥0.29 | BSD | ASGI 서버 |
| [OpenCV](https://opencv.org/) (`opencv-contrib-python`) | ≥4.9 | Apache 2.0 | 이미지 전처리, 색채 분석, 구도 분석, Saliency, Perspective Warp |
| [NumPy](https://numpy.org/) | ≥1.24 | BSD | 수치 계산, 벡터 연산 |
| [scikit-learn](https://scikit-learn.org/) | ≥1.3 | BSD | KMeans 클러스터링 (주조색 추출) |
| [Pillow](https://pillow.readthedocs.io/) | ≥10.0 | HPND | 이미지 포맷 변환, PWA 아이콘 생성 |
| [SciPy](https://scipy.org/) | ≥1.11 | BSD | 수치 최적화, 신호 처리 |
| [sentence-transformers](https://www.sbert.net/) | ≥2.6 | Apache 2.0 | CLIP ViT-B/32 모델 로딩 및 이미지 임베딩 추출 |
| [FAISS](https://faiss.ai/) (`faiss-cpu`) | ≥1.8 | MIT | 18,455개 벡터 IndexFlatIP 근접 이웃 검색 |
| [google-generativeai](https://pypi.org/project/google-generativeai/) | ≥0.5 | Apache 2.0 | Gemini API (도슨트 에세이, 채팅, 번역, 회고) |
| [google-cloud-vision](https://cloud.google.com/vision/docs/reference/libraries) | ≥2.14 | Apache 2.0 | Google Cloud Vision Web Detection |
| [python-jose](https://github.com/mpdavis/python-jose) | ≥3.3 | MIT | JWT 토큰 생성 및 검증 |
| [passlib](https://passlib.readthedocs.io/) | ≥1.7 | BSD | bcrypt 기반 비밀번호 해싱 |
| [psycopg2-binary](https://www.psycopg.org/) | ≥2.9 | LGPL | PostgreSQL 연결 (Supabase 사용 시) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ≥1.0 | BSD | `.env` 환경변수 로딩 |

#### Frontend (JavaScript)

| Library | Version | License | Usage |
|---|---|---|---|
| [React](https://react.dev/) | ^18.3 | MIT | UI 프레임워크 |
| [Vite](https://vitejs.dev/) | ^5.1 | MIT | 프론트엔드 빌드 툴 |
| [React Router](https://reactrouter.com/) | ^6.22 | MIT | SPA 클라이언트 라우팅 |
| [Axios](https://axios-http.com/) | ^1.6 | MIT | HTTP 클라이언트, 인터셉터 기반 JWT 주입 |
| [html-to-image](https://github.com/bubkoo/html-to-image) | ^1.11 | MIT | 티켓 DOM을 PNG 이미지로 변환 (저장·공유 기능) |
| [react-colorful](https://github.com/omgovich/react-colorful) | ^5.7 | MIT | HSL 색상 피커 컴포넌트 (마음색 직접 선택) |

#### Fonts

| Font | Source | License |
|---|---|---|
| **Cinzel** | [Google Fonts](https://fonts.google.com/specimen/Cinzel) | OFL |
| **Cormorant Garamond** | [Google Fonts](https://fonts.google.com/specimen/Cormorant+Garamond) | OFL |
| **Noto Serif KR** | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Serif+KR) | OFL |
| **Noto Sans KR** | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+KR) | OFL |

---

## Future Improvements

- 실제 갤러리 촬영 데이터 기반 frame detection fine-tuning
- OCR 기반 작품 라벨 인식 고도화 (한글 라벨 지원)
- 저널 검색·날짜 필터·감정 태그 필터링 기능
- 사용자별 감상 패턴 분석 리포트 (자주 느끼는 감정, 선호 색채 등)
- 다국어 도슨트 해설 (영어, 일본어)
- 작품 인식 실패 케이스를 활용한 active learning 데이터셋 구축
- 스케치 히스토리 및 시리즈 기록 기능
- 감상 통계 시각화 (캘린더 히트맵, 감정 분포 차트)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 kimseoan0516

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Third-party Licenses

이 프로젝트에서 사용하는 주요 외부 컴포넌트의 라이센스입니다.

| Component | License |
|---|---|
| React, Vite, Axios, html-to-image, react-colorful, React Router | MIT |
| FastAPI, Uvicorn, python-jose, passlib, python-dotenv, FAISS | MIT |
| OpenCV | Apache 2.0 |
| NumPy, scikit-learn, SciPy, Pillow | BSD |
| sentence-transformers | Apache 2.0 |
| google-generativeai, google-cloud-vision | Apache 2.0 |
| psycopg2-binary | LGPL |
| CLIP ViT-B/32 (via sentence-transformers) | MIT |
| Cinzel, Cormorant Garamond, Noto Serif KR, Noto Sans KR | OFL (SIL Open Font License) |
| AIC Public Domain Artworks | CC0 1.0 Universal |
| Kaggle Datasets (Best Artworks of All Time) | CC BY-NC-SA 4.0 (Kaggle 이용약관 준수) |

> **Note**: 이 프로젝트의 MIT 라이센스는 소스 코드에만 적용됩니다.  
> AIC 작품 이미지는 CC0 퍼블릭 도메인이며, Kaggle 데이터셋 이미지는 해당 데이터셋의 라이센스를 따릅니다.  
> Gemini API, Google Cloud Vision API, Roboflow API 사용 시 각 서비스의 이용약관을 준수해야 합니다.
