# ARCHITECTURE

## 1. 시스템 개요

이 시스템은 Frontend, Backend, Local LLM Runtime, SQLite DB, Harness로 구성된다.

```text
Frontend Next.js
  ↓ HTTP
Backend FastAPI
  ├─ crawler: pixiv URL 검증/수집/파싱
  ├─ services: fetch, chunking, glossary, cache, history, evaluator
  ├─ llm: LiteRT-LM client, prompt 구성, translator
  └─ db: SQLAlchemy, repository layer
  ↓
LiteRT-LM gemma4-e4b

Backend
  ↓
SQLite translation.db

Harness
  ├─ golden dataset
  ├─ smoke dataset
  ├─ rule-based evaluator
  └─ regression report
```

---

## 2. 기술 스택

### 2.1 Frontend

```text
Next.js
TypeScript
React
Tailwind CSS
shadcn/ui
TanStack Query
pnpm
```

### 2.2 Backend

```text
Python 3.11+
FastAPI
Uvicorn
Pydantic
httpx
BeautifulSoup4
selectolax
Playwright
SQLAlchemy
Alembic
SQLite
pytest
pytest-asyncio
```

### 2.3 LLM Runtime

```text
LiteRT-LM
gemma4-e4b
C:\Users\USER\.litert-lm\models\gemma4-e4b\model.litertlm
litert_lm.Engine Python API
```

### 2.4 Harness

```text
pytest
pytest-asyncio
rouge-score
sacrebleu
custom rule-based evaluator
golden dataset
prompt versioning
regression report
```

---

## 3. 권장 프로젝트 구조

```text
project-root/
├── AGENTS.md
├── README.md
├── .env.example
├── Docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DB.md
│   ├── PIXIV.md
│   ├── LLM.md
│   ├── HARNESS.md
│   ├── FRONTEND.md
│   ├── DEVELOPMENT.md
│   ├── OPERATIONS.md
│   ├── SECURITY.md
│   └── ADR/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── stores/
│   ├── package.json
│   └── tsconfig.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── crawler/
│   │   ├── llm/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── db/
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
├── harness/
│   ├── datasets/
│   ├── prompts/
│   ├── evaluators/
│   ├── reports/
│   └── run_eval.py
└── scripts/
```

---

## 4. Backend 계층 책임

### 4.1 API Routes

위치:

```text
backend/app/api/routes/
```

책임:

```text
HTTP request/response 처리
Pydantic schema 검증
service 호출
사용자 친화적 오류 응답 반환
```

API route에서 직접 SQL을 작성하지 않는다.

### 4.2 Crawler

위치:

```text
backend/app/crawler/
```

파일:

```text
pixiv_client.py
pixiv_parser.py
pixiv_types.py
url_validator.py
```

책임:

```text
pixiv URL 검증
novel ID 추출
HTML 또는 렌더링 결과 요청
페이지 데이터에서 제목/작가/본문 추출
```

네트워크 요청과 파싱 책임은 분리한다.

### 4.3 LLM Layer

위치:

```text
backend/app/llm/
```

파일:

```text
litert_lm_client.py
prompts.py
translator.py
```

책임:

```text
LiteRT-LM Engine 호출
timeout / streaming 처리
프롬프트 로딩
chunk별 번역 실행
모델 응답 정규화
```

LiteRT-LM client에는 비즈니스 로직을 넣지 않는다.

### 4.4 Services

위치:

```text
backend/app/services/
```

파일:

```text
fetch_service.py
chunker.py
glossary.py
cache.py
history.py
evaluator.py
```

책임:

```text
수집 결과 검증
translation_jobs 생성
chunk 생성
cache 조회/저장
glossary context 생성
번역 이력 조회
하네스 평가 실행
```

### 4.5 DB Layer

위치:

```text
backend/app/db/
```

파일:

```text
schema.sql
models.py
session.py
repositories/
```

DB 구조의 기준 문서는 `Docs/DB.md`이다.

Repository 예시:

```text
translation_repository.py
chunk_repository.py
glossary_repository.py
cache_repository.py
evaluation_repository.py
```

---

## 5. 주요 처리 흐름

### 5.1 pixiv URL 기반 번역 흐름

```text
User
 ↓
Frontend pixiv URL 입력
 ↓
POST /api/fetch/pixiv 또는 /api/fetch/pixiv/translate
 ↓
URL 검증
 ↓
pixiv novel ID 추출
 ↓
원문 수집
 ↓
제목 / 작가 / 작품 ID / 원문 추출
 ↓
translation_jobs 생성
 ↓
chunking
 ↓
translation_chunks 생성
 ↓
LiteRT-LM gemma4-e4b 번역
 ↓
chunk별 번역 저장
 ↓
전체 번역문 병합
 ↓
translation_jobs 완료 처리
 ↓
Frontend 결과 반환
```

### 5.2 직접 원문 입력 번역 흐름

```text
User
 ↓
Frontend 일본어 원문 입력
 ↓
POST /api/translate
 ↓
입력 검증
 ↓
Cache 확인
 ↓
Chunking
 ↓
Glossary 적용
 ↓
Prompt 구성
 ↓
LiteRT-LM gemma4-e4b 호출
 ↓
Chunk별 번역 저장
 ↓
전체 번역문 병합
 ↓
translation_jobs 저장
 ↓
Frontend 결과 반환
```

---

## 6. 의존성 방향

```text
api/routes → services → repositories → db/session
api/routes → services → llm/client
services → crawler
services → chunker/glossary/cache
llm/client → LiteRT-LM Engine
repositories → SQLAlchemy/SQLite
```

금지:

```text
Frontend → pixiv 직접 호출
Frontend → LiteRT-LM 직접 호출
api/routes → DB 직접 SQL
parser → network request
chunker → LLM 호출
litert_lm_client → DB 접근
```
