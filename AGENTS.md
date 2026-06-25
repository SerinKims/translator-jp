# AGENTS.md

이 문서는 에이전트가 프로젝트 작업을 시작할 때 가장 먼저 읽는 진입점이다.

AGENTS.md에는 상세 설계를 길게 넣지 않는다. 대신 작업 유형별로 어떤 하위 문서를 먼저 읽어야 하는지 지정한다. 구현자는 AGENTS.md만 읽고 바로 작업하지 말고, 아래 표에 해당하는 문서를 먼저 확인한 뒤 작업한다.

---

## 1. 프로젝트 한 줄 요약

이 프로젝트는 로컬 Ollama의 `gemma4:26b-a4b-it-q4_K_M` 모델을 사용하여 사용자가 입력한 일본어 원문 또는 pixiv 소설 URL의 원문을 한국어 웹소설 문체로 번역하는 웹사이트이다.

핵심 범위는 다음과 같다.

```text
pixiv 단건 URL 원문 수집
일본어 → 한국어 번역
긴 소설 chunk 번역
용어집 적용
중복 번역 캐싱
번역 이력 저장
사용자 피드백 저장
프롬프트 버전 관리
하네스 평가
SQLite 기반 로컬 저장
```

---

## 2. 작업 유형별 필독 문서

| 작업 유형                                  | 먼저 읽을 문서           | 함께 확인할 파일/영역                                                                                              |
| ------------------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| 요구사항 추가/변경                         | `Docs/PRD.md`          | `Docs/API.md`, `Docs/ARCHITECTURE.md`                                                                          |
| 전체 구조/모듈 배치 변경                   | `Docs/ARCHITECTURE.md` | `backend/app/`, `frontend/`, `harness/`                                                                      |
| API 추가/수정                              | `Docs/API.md`          | `backend/app/api/routes/`, `backend/app/schemas/`                                                              |
| DB 스키마/모델/저장 로직 변경              | `Docs/DB.md`           | `backend/app/db/schema.sql`, `backend/app/db/models.py`, `backend/app/db/repositories/`                      |
| pixiv URL 수집 기능                        | `Docs/PIXIV.md`        | `backend/app/crawler/`, `backend/app/services/fetch_service.py`, `Docs/ADR/0003-backend-only-pixiv-fetch.md` |
| 번역 품질/프롬프트/chunking/cache/glossary | `Docs/LLM.md`          | `harness/prompts/`, `backend/app/llm/`, `backend/app/services/`, `Docs/HARNESS.md`                         |
| 하네스/평가/회귀 테스트                    | `Docs/HARNESS.md`      | `harness/datasets/`, `harness/evaluators/`, `harness/reports/`                                               |
| Frontend 화면/UX                           | `Docs/FRONTEND.md`     | `frontend/app/`, `frontend/components/`, `frontend/lib/`                                                     |
| 개발 프로세스/명령어/테스트                | `Docs/DEVELOPMENT.md`  | `backend/tests/`, `scripts/`, `.env.example`                                                                 |
| 에러 처리/운영/성능                        | `Docs/OPERATIONS.md`   | `backend/app/core/logging.py`, health check, logs                                                                |
| 보안/데이터 보관/저작권 관련 처리          | `Docs/SECURITY.md`     | 로그, DB 저장 정책, pixiv 수집 정책                                                                                |
| 기술 결정 이유 확인                        | `Docs/ADR/`            | 관련 ADR 문서                                                                                                      |

---

## 3. 모든 작업에 적용되는 공통 규칙

1. **DB 관련 작업은 반드시 `Docs/DB.md`를 우선한다.**

   - `Docs/DB.md`와 실제 DB schema/model/repository가 다르면 문서를 먼저 갱신하거나 구현을 문서에 맞춘다.
2. **프롬프트는 코드에 하드코딩하지 않는다.**

   - 프롬프트 파일은 `harness/prompts/`에 둔다.
   - 프롬프트 변경 시 `Docs/LLM.md`와 `Docs/HARNESS.md` 기준으로 평가를 수행한다.
3. **pixiv 수집은 단건 URL 기반으로만 구현한다.**

   - 대량 크롤링, 랭킹/태그/작가 페이지 순회, 로그인/캡차/권한 우회 기능을 구현하지 않는다.
4. **Frontend에서 pixiv 또는 Ollama를 직접 호출하지 않는다.**

   - pixiv 수집과 Ollama 호출은 Backend를 통해서만 수행한다.
5. **긴 텍스트 번역은 chunk 상태를 DB에 저장한다.**

   - 실패 chunk만 재시도 가능해야 한다.
6. **번역 품질에 영향을 주는 변경은 하네스 평가 대상이다.**

   - prompt, chunking, glossary, cache key, model option 변경 시 smoke/golden regression을 고려한다.
7. **로그에 사용자의 긴 원문 전체를 남기지 않는다.**

   - 오류 추적용 metadata와 짧은 preview만 허용한다.
8. **새 기능 구현 전 테스트를 먼저 작성한다.**

   - API schema → DB 영향 확인 → 테스트 작성 → 최소 구현 → 테스트/하네스 실행 순서를 따른다.

---

## 4. 기본 작업 순서

```text
1. 작업 유형 확인
2. AGENTS.md의 문서 매핑 확인
3. 해당 Docs 문서 읽기
4. DB 영향이 있으면 Docs/DB.md 확인
5. API schema 또는 인터페이스 먼저 정의
6. 테스트 작성
7. 최소 구현
8. unit/integration test 실행
9. 번역 품질 영향이 있으면 harness 실행
10. 문서 업데이트
11. Conventional Commits 형식으로 커밋
```

---

## 5. 금지 사항 요약

```text
pixiv 대량 크롤링 구현 금지
로그인/결제/연령/권한/캡차 우회 구현 금지
수집 원문 재배포 기능 구현 금지
원문 또는 번역문을 외부 API로 전송 금지
프롬프트 코드 하드코딩 금지
하네스 없이 프롬프트 품질 변경 금지
테스트 없이 chunking 로직 수정 금지
Docs/DB.md와 다른 DB 구조 임의 적용 금지
모델 오류를 단순 500 에러로만 반환 금지
```

---

## 6. 문서 수정 원칙

- 요구사항이 바뀌면 `Docs/PRD.md`를 수정한다.
- API 계약이 바뀌면 `Docs/API.md`를 수정한다.
- 구조나 모듈 책임이 바뀌면 `Docs/ARCHITECTURE.md`를 수정한다.
- DB 구조가 바뀌면 `Docs/DB.md`를 수정한다.
- pixiv 수집 정책이나 구현 방식이 바뀌면 `Docs/PIXIV.md`와 관련 ADR을 수정한다.
- 프롬프트, chunking, glossary, cache 정책이 바뀌면 `Docs/LLM.md`와 `Docs/HARNESS.md`를 수정한다.
- 장기적으로 유지할 기술 결정은 `Docs/ADR/`에 ADR로 남긴다.

AGENTS.md는 상세 내용을 중복하지 않고, 문서 읽기 순서와 공통 규칙만 유지한다.
