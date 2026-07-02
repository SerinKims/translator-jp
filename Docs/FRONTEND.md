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
용어집 관리 화면
사용자 피드백 입력 화면
```

---

## 3. 기본 화면 구성

```text
pixiv URL 입력 영역
직접 일본어 원문 입력 영역
원문 언어 선택 영역
번역 옵션 영역
번역 실행 버튼
한국어 결과 영역
원문/번역 병렬 보기 영역
chunk 진행 상태
복사 버튼
다음화 번역 버튼
전체 번역 버튼
번역 이력
용어집 관리
피드백 입력
에러 메시지 영역
```

MVP Frontend에서는 원문 가져오기 버튼과 번역 실행 버튼을 분리하지 않는다.
사용자는 `번역 실행` 버튼 하나만 사용한다.

입력 우선순위:

```text
1. pixiv URL
2. 직접 입력 텍스트
```

pixiv URL과 직접 입력 텍스트가 모두 있으면 pixiv URL 기반 번역을 실행한다.
둘 다 비어 있으면 다음 메시지를 표시한다.

```text
pixiv URL 또는 번역할 텍스트를 입력해주세요.
```

---

## 4. UX 규칙

```text
번역 중에는 번역 실행 버튼을 비활성화한다.
긴 텍스트 번역 중에는 진행 상태를 표시한다.
API 오류는 사용자가 이해할 수 있는 메시지로 보여준다.
Ollama을 사용할 수 없으면 명확히 안내한다.
모델이 없으면 설치 명령을 안내한다.
pixiv URL이 잘못되었으면 올바른 예시를 보여준다.
pixiv 원문 수집에 실패하면 직접 원문 입력을 안내한다.
결과가 비어 있으면 재시도 버튼을 제공한다.
```

진행 상태 예시:

```text
원문을 가져오는 중입니다...
번역을 준비하는 중입니다...
번역 중입니다...
번역이 완료되었습니다.
```

원문 언어 선택:

```text
자동 감지: auto
일본어: ja
중국어 간체: zh-CN
중국어 번체: zh-TW
영어: en
```

목표 언어는 MVP에서 한국어(`ko`)로 고정한다.

번역 요청 기본 옵션:

```text
translate_scope=first_page
page_index=0
style=webnovel
honorific_policy=preserve
preserve_names=true
use_glossary=true
use_cache=true
stream=false
```

`[newpage]`가 감지되어 `total_pages > 1`이면 첫 실행에서는 첫 page만
번역한다. `has_next_page=true`이면 `다음화 번역` 버튼을 표시하고
`POST /api/translations/{job_id}/pages/{page_index}/translate`를 호출한다.
전체 번역은 사용자가 경고를 확인한 경우에만 남은 page를 순차 호출한다.

번역 결과 기본 보기는 원문/번역 병렬 보기이다.

```text
Desktop: 왼쪽 50% 원문, 오른쪽 50% 번역문
Mobile: 원문과 번역문을 위아래로 표시
```

보기 모드는 다음 두 가지를 지원한다.

```text
원문+번역
번역만
```

API의 초기 번역 응답에 chunk 본문이 없을 수 있으므로, Frontend는 번역 성공
직후 `GET /api/translations/{job_id}`를 호출해 상세 응답의 `pages`와
`chunks`를 병렬 보기 데이터로 사용한다.

복사 기능:

```text
번역문만 복사
원문+번역 함께 복사
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

모든 수집/번역 작업은 Backend API를 통해 수행한다.

Frontend 개발 서버는 Next.js rewrite로 same-origin `/api/*` 요청을 Backend
`/api/*`로 전달한다. 기본 Backend 주소는 `http://localhost:8000`이며
`BACKEND_URL` 환경 변수로 변경할 수 있다.

---

## 2026-07-02 번역 옵션 및 페이지 이동 UI

- 번역 스타일은 `webnovel`, `literal`, `natural` 프리셋을 제공하고 직접 입력도 허용한다.
- 존댓말/반말 정책은 `preserve`, `formal`, `casual` 프리셋을 제공하고 직접 입력도 허용한다.
- 용어집 사용 여부는 번역 옵션에서 켜고 끌 수 있으며, 텍스트/pixiv/페이지 번역 요청에 같은 값으로 전달한다.
- 다중 페이지 결과에서는 이전 페이지와 다음 페이지 버튼으로 표시 페이지만 이동한다.
- 미번역 페이지로 이동한 경우 별도의 현재 페이지 번역 버튼으로 해당 페이지 번역을 실행한다.

## 2026-07-02 용어집 비활성 항목 UI

- 사이드 용어집 관리에서는 활성 용어와 비활성 용어를 분리해서 보여준다.
- 비활성 용어는 기본적으로 접어 두고, `비활성 용어 보기` 버튼으로 확인한다.
- 비활성 용어의 `재활성화` 버튼은 `PATCH /api/glossary/{term_id}`에 `is_active=true`를 보내 해당 용어를 다시 번역 용어집 선택 대상에 포함한다.
