# PIXIV 수집 정책 및 설계

## 1. 기본 원칙

pixiv 수집 기능은 사용자가 직접 입력한 소설 URL 1건을 처리하기 위한 기능이다.

허용 범위:

```text
사용자가 직접 입력한 pixiv 소설 URL 접근
사용자가 접근 가능한 공개 또는 로그인 세션 기반 페이지 처리
소설 원문, 제목, 작가명, 작품 ID 등 번역에 필요한 정보 추출
번역 작업 생성을 위한 원문 저장
사용자 개인 번역 이력 저장
```

금지 범위:

```text
pixiv 전체 사이트 대량 크롤링
태그, 랭킹, 작가 페이지를 순회하며 대량 수집
로그인, 결제, 연령 제한, 권한 제한 우회
캡차 우회
robots.txt 또는 접근 제어 우회
비정상적인 고속 요청
수집 원문 재배포
수집 원문을 학습 데이터셋으로 무단 사용
프론트엔드에서 pixiv를 직접 크롤링
```

---

## 2. 요청 제한

pixiv 수집은 단건 요청 중심으로 제한한다.

권장 제한:

```text
동시 수집 요청: 1개
요청 간 최소 대기 시간: 3초 이상
동일 URL 재수집: 캐시 우선 사용
실패 시 재시도: 최대 2회
timeout: 30초
```

---

## 3. 접근 방식

기본 접근 방식은 Backend에서 수행한다.

우선순위:

```text
1. 정적 HTML에서 원문 추출 가능 여부 확인
2. 필요한 경우 Playwright 기반 브라우저 렌더링 사용
3. 사용자가 직접 제공한 접근 가능한 URL만 처리
4. 로그인 정보는 서버에 저장하지 않음
```

로그인이 필요한 작품의 경우 구현 방식은 다음 중 하나를 선택한다.

```text
사용자가 브라우저에서 직접 열람 가능한 원문을 복사하여 입력
또는 로컬 환경에서만 사용자가 직접 준비한 세션을 사용
```

에이전트는 로그인 우회, 인증 우회, 캡차 우회 기능을 구현하면 안 된다.

---

## 4. URL Validator

파일:

```text
backend/app/crawler/url_validator.py
```

책임:

```text
입력 URL 검증
pixiv 도메인 검증
novel URL 여부 확인
novel ID 추출
URL 정규화
```

허용 URL 예시:

```text
https://www.pixiv.net/novel/show.php?id=12345678
https://www.pixiv.net/novel/series/1234567
```

MVP에서는 단일 소설 URL만 지원한다.

MVP 지원 대상:

```text
/novel/show.php?id={novel_id}
```

시리즈 URL은 추후 확장 대상으로 둔다.

지원하지 않는 URL은 명확히 거부한다.

사용자 메시지:

```text
지원하지 않는 pixiv URL입니다. 소설 상세 페이지 URL을 입력해주세요.
```

---

## 5. Pixiv Client

파일:

```text
backend/app/crawler/pixiv_client.py
```

책임:

```text
pixiv 페이지 요청
timeout 처리
rate limit 적용
HTTP 에러 처리
HTML 또는 렌더링 결과 반환
필요 시 Playwright 렌더링
```

금지:

```text
로그인 우회
캡차 우회
대량 페이지 순회
무제한 재시도
```

---

## 6. Pixiv Parser

파일:

```text
backend/app/crawler/pixiv_parser.py
```

책임:

```text
HTML 또는 페이지 데이터에서 제목 추출
작가명 추출
소설 원문 추출
작품 ID 추출
태그 추출 가능 시 추출
본문 정리
문단 구조 보존
불필요한 UI 텍스트 제거
```

parser는 네트워크 요청을 직접 수행하지 않는다.

---

## 7. Fetch Service

파일:

```text
backend/app/services/fetch_service.py
```

책임:

```text
URL 검증
pixiv_client 호출
pixiv_parser 호출
수집 결과 검증
translation_jobs 생성
필요 시 바로 번역 서비스 호출
```

---

## 8. DB 저장 metadata

pixiv 수집 기능은 `translation_jobs`에 source metadata를 저장한다.

필수 후보:

```text
source_site
source_url
source_title
source_author
source_work_id
source_fetched_at
```

DB 구조의 최종 기준은 `Docs/DB.md`이다.

---

## 9. 오류 코드

| 상황 | 사용자 메시지 | 로그 코드 |
|---|---|---|
| URL 오류 | 지원하지 않는 pixiv URL입니다. 소설 상세 페이지 URL을 입력해주세요. | `PIXIV_INVALID_URL` |
| 수집 실패 | pixiv 원문을 가져오지 못했습니다. URL을 확인하거나 원문을 직접 입력해주세요. | `PIXIV_FETCH_FAILED` |
| 접근 제한 | 해당 pixiv 페이지에 접근할 수 없습니다. 브라우저에서 열람 가능한 페이지인지 확인해주세요. | `PIXIV_ACCESS_DENIED` |
| 원문 추출 실패 | 페이지는 열렸지만 소설 원문을 찾지 못했습니다. 원문을 직접 입력해주세요. | `PIXIV_PARSE_FAILED` |
