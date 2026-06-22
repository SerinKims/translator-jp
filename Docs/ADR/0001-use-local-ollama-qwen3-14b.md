# ADR 0001: 로컬 Ollama + qwen3:14b 사용

## Status

Accepted

## Context

이 프로젝트는 일본어 웹소설 원문을 한국어로 번역한다. pixiv에서 가져온 원문은 저작권과 개인정보성 맥락이 있을 수 있으므로 외부 API로 전송하지 않는 것이 기본 정책이다.

## Decision

기본 LLM Runtime은 로컬 Ollama로 설정하고, 기본 모델은 `qwen3:14b`로 사용한다.

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:14b
```

Backend가 Ollama API를 호출하며, Frontend는 Ollama를 직접 호출하지 않는다.

## Consequences

장점:

```text
원문 외부 전송 방지
로컬 환경에서 반복 테스트 가능
프롬프트/하네스 실험 비용 감소
```

단점:

```text
사용자 로컬 머신 성능에 따라 응답 시간이 달라진다.
긴 소설 번역은 chunking과 진행 상태 표시가 필요하다.
모델 설치 및 실행 상태를 health check로 확인해야 한다.
```
