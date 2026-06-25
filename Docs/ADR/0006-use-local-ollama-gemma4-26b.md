# ADR 0006: 로컬 Ollama + gemma4:26b-a4b-it-q4_K_M 사용

## Status

Accepted

## Context

이 프로젝트는 일본어 웹소설 원문을 한국어로 번역한다. 원문과 번역문을 외부 API로 전송하지 않는 정책은 유지하되, 기본 LLM Runtime과 모델을 LiteRT-LM `gemma4-e4b`에서 Ollama `gemma4:26b-a4b-it-q4_K_M`로 교체한다.

## Decision

기본 LLM Runtime은 로컬 Ollama로 설정하고, 기본 모델은 `gemma4:26b-a4b-it-q4_K_M`로 사용한다.

```text
OLLAMA_MODEL_NAME=gemma4:26b-a4b-it-q4_K_M
OLLAMA_TIMEOUT_SECONDS=120
OLLAMA_HEALTH_TIMEOUT_SECONDS=3
```

Backend가 `ollama.chat`을 통해 모델을 호출하며, Frontend는 Ollama를 직접 호출하지 않는다.
`think`는 `str` 또는 `bool`로, `options`는 `dict`로 번역 요청자가 직접 지정할 수 있다. `think` 기본값은 `False`이다.

## Consequences

장점:

```text
원문 외부 전송 방지
Ollama 모델 이름만으로 런타임과 모델 교체 가능
test.py와 같은 ollama.chat 호출 방식으로 smoke test와 backend 구현 일치
```

단점:

```text
사용자 로컬 머신 성능과 Ollama 실행 상태에 따라 응답 시간이 달라진다.
긴 소설 번역은 chunking과 진행 상태 표시가 필요하다.
Ollama 패키지 설치 상태와 로컬 모델 준비 상태를 구분해 안내해야 한다.
```
