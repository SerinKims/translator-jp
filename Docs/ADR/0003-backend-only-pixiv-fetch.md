# ADR 0003: pixiv 수집은 Backend 단건 URL 기반으로만 수행

## Status

Accepted

## Context

프로젝트는 사용자가 입력한 pixiv 소설 URL에서 번역에 필요한 원문과 metadata를 가져온다. 다만 대량 크롤링, 접근 제어 우회, 재배포 기능은 프로젝트 범위가 아니다.

## Decision

pixiv 수집은 Backend에서만 수행한다.

MVP 지원 범위:

```text
https://www.pixiv.net/novel/show.php?id={novel_id}
```

수집은 사용자가 직접 입력한 단건 URL 중심으로 제한한다.

## Consequences

장점:

```text
수집 정책을 Backend에서 일관되게 통제할 수 있다.
rate limit, timeout, retry, error handling을 중앙화할 수 있다.
Frontend에 pixiv 파싱 로직이 노출되지 않는다.
```

제한:

```text
시리즈 URL은 후속 확장 대상이다.
로그인/캡차/권한 우회는 구현하지 않는다.
접근 불가 페이지는 직접 원문 입력을 안내한다.
```
