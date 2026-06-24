# PRD: 일본어 → 한국어 웹소설 번역 사이트

## 1. 목적

사용자가 입력한 일본어 원문 또는 pixiv 소설 URL에서 수집한 원문을 로컬 LLM으로 한국어 웹소설 문체로 번역한다.

목표는 단순 직역이 아니라 일본 소설 특유의 문체, 대사, 감정선, 존댓말/반말 관계, 고유명사, 장르 용어를 자연스러운 한국어 웹소설 문체로 변환하는 것이다.

---

## 2. 주요 사용자 흐름

### 2.1 pixiv URL 기반 번역

```text
사용자가 pixiv 소설 URL 입력
→ Backend가 URL 검증
→ novel ID 추출
→ 접근 가능한 페이지에서 원문/제목/작가/작품 ID 수집
→ translation_jobs 생성
→ chunking
→ gemma4-e4b 번역
→ chunk별 결과 저장
→ 전체 번역문 병합
→ Frontend에 결과 표시
```

### 2.2 직접 원문 입력 번역

```text
사용자가 일본어 원문 입력
→ Backend 입력 검증
→ cache 확인
→ chunking
→ glossary 적용
→ prompt 구성
→ LiteRT-LM gemma4-e4b 호출
→ chunk별 결과 저장
→ 전체 번역문 병합
→ Frontend에 결과 표시
```

---

## 3. 기능 요구사항

### 3.1 원문 수집

- 사용자는 pixiv 소설 URL을 입력할 수 있다.
- Backend는 입력 URL이 지원 가능한 pixiv 소설 상세 URL인지 검증한다.
- URL에서 pixiv novel ID를 추출한다.
- 접근 가능한 페이지에서 소설 원문을 수집한다.
- 제목, 작가명, 작품 ID, URL, 수집 시각을 함께 저장한다.
- 수집된 원문으로 번역 작업을 생성할 수 있다.
- 수집 실패 시 사용자가 이해할 수 있는 오류 메시지를 반환한다.

### 3.2 번역

- 일본어 원문 직접 입력과 pixiv URL 입력을 모두 지원한다.
- 한국어 번역 결과를 출력한다.
- 긴 텍스트는 chunk 단위로 번역한다.
- 문단 순서를 유지한다.
- 대사, 독백, 설명문을 최대한 구분한다.
- 번역 옵션을 제공한다.

번역 옵션:

```text
웹소설체
직역에 가까운 번역
자연스러운 의역
존댓말/반말 유지
고유명사 보존
용어집 적용
캐시 사용
```

### 3.3 저장 및 관리

- 번역 작업 이력을 저장한다.
- chunk별 번역 상태를 저장한다.
- 실패 chunk만 재시도할 수 있다.
- 중복 번역을 캐싱한다.
- 용어집을 관리한다.
- 사용자 수정/피드백을 저장한다.
- 하네스 평가를 실행하고 결과를 저장한다.

---

## 4. 비기능 요구사항

- 로컬 LLM 기반으로 동작한다.
- 기본 모델은 `gemma4-e4b`이다.
- LiteRT-LM Python API를 통해 모델을 호출한다.
- 모델 API 장애 시 명확한 오류를 표시한다.
- pixiv 수집 장애 시 명확한 오류를 표시한다.
- 긴 입력은 자동 chunking 처리한다.
- chunk 간 용어, 말투, 인칭 일관성을 유지한다.
- 번역 결과는 원문 순서를 유지한다.
- 프롬프트 변경 시 기존 golden test 결과와 비교 가능해야 한다.
- 모델 응답 시간과 실패 로그를 저장한다.
- 전체 원문을 불필요하게 로그에 남기지 않는다.
- pixiv에서 가져온 원문을 외부 API로 전송하지 않는다.
- pixiv 원문은 사용자의 번역 목적 범위에서만 저장한다.

---

## 5. 품질 기준

### 5.1 좋은 번역

```text
한국어 문장이 자연스럽다.
일본어 원문의 감정선이 유지된다.
인물 간 말투 관계가 유지된다.
설명문과 대사체가 구분된다.
고유명사가 임의 변경되지 않는다.
용어집을 준수한다.
원문에 없는 내용을 추가하지 않는다.
문단 순서를 유지한다.
```

### 5.2 나쁜 번역

```text
원문 일부가 누락된다.
일본어가 그대로 남아 있다.
문단 순서가 바뀐다.
대사가 설명문으로 바뀐다.
존댓말/반말 관계가 깨진다.
너무 요약된다.
원문에 없는 설정을 추가한다.
고유명사가 임의 변경된다.
용어집을 위반한다.
```

---

## 6. MVP 범위

1차 구현 범위:

```text
FastAPI Backend 기본 구조
SQLite DB 초기화
/api/health
pixiv 단일 소설 URL validator
pixiv 원문 수집 API
직접 원문 번역 API
LiteRT-LM gemma4-e4b 호출
chunking
translation_jobs / translation_chunks 저장
기본 Frontend 입력/결과 화면
최소 smoke harness
```

후속 구현 범위:

```text
glossary_terms 적용
translation_cache 적용
translation_feedback 저장
chunk 재시도 기능
번역 이력 상세 조회
prompt versioning
regression report 저장
```

---

## 7. Definition of Done

```text
pixiv 소설 URL에서 원문을 가져올 수 있다.
가져온 원문이 translation_jobs에 저장된다.
로컬에서 gemma4-e4b로 일본어 → 한국어 번역이 가능하다.
긴 소설 텍스트도 chunk 단위로 안정적으로 번역된다.
Frontend에서 pixiv URL 입력, 원문 수집, 번역 요청, 결과 확인이 가능하다.
translation_jobs에 번역 작업과 source metadata가 저장된다.
translation_chunks에 chunk별 결과가 저장된다.
용어집을 적용할 수 있다.
translation_cache로 중복 번역을 방지할 수 있다.
/api/health로 LiteRT-LM 실행 준비 상태와 DB 연결 상태를 확인할 수 있다.
최소 10개 이상의 smoke case가 harness에서 실행된다.
prompt 변경 시 regression report를 생성할 수 있다.
Docs/DB.md와 실제 DB 구조가 일치한다.
README 또는 AGENTS.md의 실행 명령이 최신 상태이다.
```
