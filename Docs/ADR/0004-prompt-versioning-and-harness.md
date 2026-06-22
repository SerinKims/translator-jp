# ADR 0004: 프롬프트 버전 관리와 하네스 회귀 평가

## Status

Accepted

## Context

번역 품질은 프롬프트, chunking, glossary, cache 정책, 모델 옵션에 영향을 받는다. 변경이 좋아 보이더라도 기존 케이스에서 품질이 악화될 수 있다.

## Decision

프롬프트는 파일로 관리하고, 번역 결과에는 prompt version을 저장한다.

```text
harness/prompts/translate_v1.md
```

프롬프트 또는 번역 품질에 영향을 주는 변경 후에는 하네스 평가를 수행한다.

```text
smoke_cases.jsonl
golden_ja_ko.jsonl
eval_runs
eval_results
harness/reports/
```

## Consequences

장점:

```text
프롬프트 변경 이력을 추적할 수 있다.
회귀 품질 저하를 조기에 발견할 수 있다.
사용자 피드백을 golden dataset 후보로 전환할 수 있다.
```

단점:

```text
프롬프트 변경에도 테스트/평가 시간이 필요하다.
평가 기준을 지속적으로 보정해야 한다.
```
