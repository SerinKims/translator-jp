# FRONTEND

## 1. 기술 스택

```text
Next.js
TypeScript
React
Tailwind CSS
shadcn/ui
TanStack Query
pnpm
```

---

## 2. Frontend 역할

```text
pixiv URL 입력 UI
직접 원문 입력 UI
번역 옵션 선택 UI
수집 요청 전송
번역 요청 전송
번역 결과 표시
chunk 진행 상태 표시
번역 이력 조회
번역 이력 단건/전체 삭제
용어집 추가/수정/비활성화/재활성화/영구 삭제 관리 화면
용어집 UTF-8 CSV import 및 등록/중복/충돌 결과 확인
사용자 피드백 입력 화면
```

---

## 3. 기본 화면 구성

```text
pixiv URL 입력 영역
직접 일본어 원문 입력 영역
번역 옵션 영역
원문 가져오기 버튼
번역 실행 버튼
한국어 결과 영역
chunk 진행 상태
복사 버튼
번역 이력
용어집 관리
피드백 입력
에러 메시지 영역
```

---

## 4. UX 규칙

```text
원문 수집 중에는 가져오기 버튼을 비활성화한다.
번역 중에는 번역 버튼을 비활성화한다.
긴 텍스트 번역 중에는 진행 상태를 표시한다.
API 오류는 사용자가 이해할 수 있는 메시지로 보여준다.
용어 영구 삭제 버튼은 비활성 용어에만 표시한다.
용어 영구 삭제 전 원문 용어와 복구 불가 안내를 포함한 확인창을 표시한다.
용어 삭제 요청 중에는 중복 요청을 막고, 성공 후 목록 캐시와 해당 수정 폼을 초기화한다.
용어 CSV import는 `.csv` 파일을 UTF-8 텍스트로 읽어 Backend API로 전송한다.
용어 CSV import 중에는 중복 요청과 다른 용어 변경을 막는다.
용어 CSV import 완료 후 등록/중복/충돌 건수와 충돌 행별 상세를 표시하고 용어 목록을 갱신한다.
Ollama을 사용할 수 없으면 명확히 안내한다.
모델이 없으면 설치 명령을 안내한다.
pixiv URL이 잘못되었으면 올바른 예시를 보여준다.
pixiv 원문 수집에 실패하면 직접 원문 입력을 안내한다.
결과가 비어 있으면 재시도 버튼을 제공한다.
```

---

## 5. 사용자 메시지 예시

```text
Ollama를 사용할 수 없습니다. backend requirements와 로컬 Ollama 실행 상태를 확인해주세요.
```

```text
gemma4:26b-a4b-it-q4_K_M 모델을 찾을 수 없습니다. ollama pull 명령으로 모델을 준비해주세요.
```

```text
pixiv 원문을 가져오지 못했습니다. URL을 확인하거나 원문을 직접 입력해주세요.
```

```text
지원하지 않는 pixiv URL입니다. 소설 상세 페이지 URL을 입력해주세요.
```

---

## 6. 호출 제한

Frontend는 다음 API를 직접 호출하지 않는다.

```text
pixiv
Ollama
```

---

## 7. 2026-07-06 Translation API Payload Settings

Frontend sends user-configured request settings to Backend translation and
pixiv fetch APIs instead of keeping them as fixed UI-only values.

```text
model_name
source_lang
target_lang
style
honorific_policy
preserve_names
use_glossary
use_cache
think
options
```

Frontend does not send `prompt_version` in normal translation or pixiv fetch
requests. Backend resolves it from the selected or auto-detected source
language and returns the applied value for display/history.

`client_options` remains a frontend-only state restore field and is removed
before the backend payload is sent.

모든 수집/번역 작업은 Backend API를 통해 수행한다.
