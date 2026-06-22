# ADR 0002: SQLite와 Repository Layer 사용

## Status

Accepted

## Context

초기 개발 환경은 로컬 중심이며, 번역 작업/ chunk / 용어집 / 캐시 / 피드백 / 평가 결과를 저장해야 한다.

## Decision

초기 DB는 SQLite를 사용한다.

```text
DATABASE_URL=sqlite:///./translation.db
```

DB 접근은 repository layer를 통해 수행한다.

```text
backend/app/db/repositories/
```

DB 구조 기준 문서는 `Docs/DB.md`이다.

## Consequences

장점:

```text
로컬 개발이 단순하다.
별도 DB 서버 없이 빠르게 MVP를 구현할 수 있다.
테스트 환경 구성이 쉽다.
```

단점:

```text
동시성/확장성은 제한적이다.
향후 다중 사용자나 서버 배포를 고려할 경우 DB 전환 ADR이 필요하다.
```

## Rules

```text
API route에서 직접 SQL 작성 금지
DB schema 변경 시 Docs/DB.md 수정 필수
schema.sql, models.py, repositories 동기화 필수
```
