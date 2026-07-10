# translator-jp

로컬 Ollama의 `gemma4:26b-a4b-it-q4_K_M` 모델을 사용해 일본어 원문 또는 pixiv 소설 단건 URL의 원문을 한국어 웹소설 문체로 번역하는 로컬 웹사이트입니다.

## 원칙

- Docker는 사용하지 않습니다.
- Frontend는 pixiv 또는 Ollama를 직접 호출하지 않습니다.
- 프롬프트는 코드에 하드코딩하지 않고 `harness/prompts/`에서 관리합니다.
- DB 구조는 `Docs/DB.md`와 `backend/app/db/schema.sql`을 기준으로 합니다.
- pixiv 수집은 사용자가 입력한 단건 소설 상세 URL만 처리합니다.

## 빠른 실행

Windows PowerShell:

```powershell
.\run.ps1
```

기본값은 conda 환경 `tr-jp`입니다. conda는 플러그인 오류를 피하기 위해 `--no-plugins`로 호출합니다. `tr-jp`가 없으면 `python=3.11`과 `pip`를 포함해 새로 생성합니다. 이후 `backend/requirements.txt`를 기준으로 설치되지 않은 Python 패키지만 `tr-jp` 안에 설치합니다. base 환경에는 설치하지 않습니다.

첫 실행이면 `.env`, DB, frontend 환경 파일과 frontend 의존성을 준비한 뒤 backend/frontend 개발 서버를 각각 새 PowerShell 창으로 실행합니다.

수동으로 나누어 실행하려면:

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

다른 conda 환경을 쓰려면:

```powershell
.\run.ps1 -CondaEnv my-env
```

강제로 `.venv`를 쓰려면:

```powershell
.\run.ps1 -UseVenv
```

setup 확인을 생략하고 바로 서버만 띄우려면:

```powershell
.\run.ps1 -SkipSetup
```

명령 프롬프트 또는 더블클릭용 래퍼:

```cmd
run.cmd
```

실행 후 접속 주소:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

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
  --prompt harness/prompts/translate_ja_ko_v1.md \
  --model gemma4:26b-a4b-it-q4_K_M
```

Harness regression:

```bash
python harness/run_eval.py \
  --dataset harness/datasets/golden_ja_ko.jsonl \
  --prompt harness/prompts/translate_ja_ko_v1.md \
  --model gemma4:26b-a4b-it-q4_K_M \
  --output harness/reports/latest.json
```
