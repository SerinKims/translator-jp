# DEVELOPMENT

## 1. 개발 원칙

```text
기능 구현 전 테스트를 먼저 작성한다.
API 스키마를 먼저 정의한다.
프롬프트는 코드에 하드코딩하지 않는다.
DB 구조는 Docs/DB.md를 기준으로 한다.
pixiv 수집 기능은 단건 URL 기반으로 제한한다.
번역 품질에 영향을 주는 변경은 반드시 harness를 실행한다.
모델 출력은 비결정적이므로 rule-based check와 golden sample 비교를 병행한다.
실패한 테스트는 원인 유형을 기록한다.
```

---

## 2. 작업 순서

```text
1. 요구사항 확인
2. Docs/DB.md 확인
3. API 스키마 작성
4. DB schema / model 영향 확인
5. 테스트 작성
6. 최소 구현
7. unit test 실행
8. integration test 실행
9. harness smoke test 실행
10. frontend 연결
11. 긴 텍스트 테스트
12. regression test 실행
13. 문서 업데이트
14. 커밋
```

---

## 3. 브랜치 전략

```text
main        안정 버전
develop     통합 개발
feature/*   기능 개발
fix/*       버그 수정
eval/*      하네스 / 프롬프트 평가
docs/*      문서 수정
```

---

## 4. 커밋 메시지 규칙

Conventional Commits를 사용한다.

```text
feat: add pixiv fetch api
feat: add pixiv novel parser
feat: add translation api
feat: add glossary repository
fix: handle pixiv fetch timeout
fix: handle ollama timeout
test: add pixiv url validator tests
test: add glossary regression cases
refactor: split pixiv parser
docs: update db design
chore: update local scripts
```

---

## 5. 환경 변수 예시

`.env.example`

```env
APP_ENV=local
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:14b
OLLAMA_TIMEOUT_SECONDS=120

MAX_CHARS_PER_CHUNK=1800
CHUNK_OVERLAP_PARAGRAPHS=1

DATABASE_URL=sqlite:///./translation.db

PROMPT_VERSION=translate_v1
LOG_LEVEL=INFO

SAVE_RAW_MODEL_RESPONSE=true
CACHE_ENABLED=true

PIXIV_FETCH_ENABLED=true
PIXIV_FETCH_TIMEOUT_SECONDS=30
PIXIV_FETCH_MIN_INTERVAL_SECONDS=3
PIXIV_FETCH_MAX_RETRIES=2
PIXIV_USE_PLAYWRIGHT=false
```

---

## 6. 명령어

### 6.1 모델 설치

```bash
ollama pull qwen3:14b
```

### 6.2 Ollama 실행 확인

```bash
ollama list
curl http://localhost:11434/api/tags
```

### 6.3 Backend 가상환경 생성

```bash
cd backend
python -m venv .venv
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 6.4 Backend 패키지 설치

```bash
cd backend
pip install -r requirements.txt
```

### 6.5 Playwright 설치

pixiv 페이지 렌더링이 필요한 경우 Playwright를 사용한다.

```bash
cd backend
playwright install chromium
```

### 6.6 DB 초기화

```bash
sqlite3 backend/translation.db < backend/app/db/schema.sql
```

또는 스크립트가 있는 경우:

```bash
bash scripts/init_db.sh
```

### 6.7 Backend 실행

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6.8 Frontend 패키지 설치

```bash
cd frontend
pnpm install
```

### 6.9 Frontend 실행

```bash
cd frontend
pnpm dev
```

### 6.10 Backend 테스트

```bash
cd backend
pytest -q
```

### 6.11 특정 테스트 실행

```bash
cd backend
pytest tests/test_pixiv_url_validator.py -q
pytest tests/test_pixiv_parser.py -q
pytest tests/test_chunker.py -q
pytest tests/test_glossary.py -q
pytest tests/test_translation_api.py -q
```

### 6.12 Backend Lint / Format

```bash
cd backend
ruff check .
black .
mypy app
```

### 6.13 Frontend Lint / Format

```bash
cd frontend
pnpm lint
pnpm format
```

---

## 7. 테스트 작성 지침

### 7.1 Unit Test

대상:

```text
pixiv URL validator
pixiv novel ID extractor
pixiv parser
chunker
glossary
cache key generator
prompt loader
request schema
response schema
rule evaluator
repository
```

### 7.2 Integration Test

대상:

```text
/api/health
/api/fetch/pixiv
/api/fetch/pixiv/translate
/api/translate
/api/translations
/api/glossary
Ollama 연결
DB 저장
긴 텍스트 번역
chunk 재시도
```

### 7.3 Regression Test

대상:

```text
golden dataset
prompt version 변경
model option 변경
chunk size 변경
glossary 변경
cache 정책 변경
pixiv parser 변경
```
