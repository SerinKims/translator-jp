# translator-jp

로컬 Ollama의 `qwen3:14b` 모델을 사용해 일본어 원문 또는 pixiv 소설 단건 URL의 원문을 한국어 웹소설 문체로 번역하는 로컬 웹사이트입니다.

## 원칙

- Docker는 사용하지 않습니다.
- Frontend는 pixiv 또는 Ollama API를 직접 호출하지 않습니다.
- 프롬프트는 코드에 하드코딩하지 않고 `harness/prompts/`에서 관리합니다.
- DB 구조는 `Docs/DB.md`와 `backend/app/db/schema.sql`을 기준으로 합니다.
- pixiv 수집은 사용자가 입력한 단건 소설 상세 URL만 처리합니다.

## Backend 실행 초안

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Frontend 실행 초안

```bash
cd frontend
pnpm install
pnpm dev
```

## DB 초기화 초안

```bash
sqlite3 backend/translation.db < backend/app/db/schema.sql
```

또는:

```bash
bash scripts/init_db.sh
```

## 테스트 실행 초안

Backend:

```bash
cd backend
pytest -q
```

Harness smoke:

```bash
python harness/run_eval.py \
  --dataset harness/datasets/smoke_cases.jsonl \
  --prompt harness/prompts/translate_v1.md \
  --model qwen3:14b
```

Harness regression:

```bash
python harness/run_eval.py \
  --dataset harness/datasets/golden_ja_ko.jsonl \
  --prompt harness/prompts/translate_v1.md \
  --model qwen3:14b \
  --output harness/reports/latest.json
```
