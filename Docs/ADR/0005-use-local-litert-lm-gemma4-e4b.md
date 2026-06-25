# ADR 0005: 로컬 LiteRT-LM + gemma4-e4b 사용

## Status

Superseded by ADR 0006

## Context

이 프로젝트는 일본어 웹소설 원문을 한국어로 번역한다. 원문과 번역문을 외부 API로 전송하지 않는 정책은 유지하되, 기본 LLM Runtime과 모델을 Ollama `qwen3:14b`에서 LiteRT-LM `gemma4-e4b`로 교체한다.

## Decision

기본 LLM Runtime은 로컬 LiteRT-LM으로 설정하고, 기본 모델은 `gemma4-e4b`로 사용한다.

```text
LITERT_LM_MODEL_NAME=gemma4-e4b
LITERT_LM_MODEL_PATH=C:\Users\USER\.litert-lm\models\gemma4-e4b\model.litertlm
LITERT_LM_TIMEOUT_SECONDS=120
```

Backend가 `litert_lm.Engine`을 통해 모델을 호출하며, Frontend는 LiteRT-LM을 직접 호출하지 않는다.

## Consequences

장점:

```text
원문 외부 전송 방지
별도 Ollama HTTP 서버 없이 로컬 모델 파일 기반 실행 가능
프롬프트/하네스 실험 비용 감소
```

단점:

```text
사용자 로컬 머신 성능에 따라 응답 시간이 달라진다.
긴 소설 번역은 chunking과 진행 상태 표시가 필요하다.
모델 파일 경로와 litert-lm-api 패키지 설치 상태를 health check로 확인해야 한다.
```
