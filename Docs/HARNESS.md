# HARNESS Engineering

## 1. 목적

하네스는 단순 테스트가 아니라 번역 품질을 지속적으로 검증하는 평가 시스템이다.

프롬프트, 모델 옵션, chunking, glossary, cache 정책이 변경될 때 기존 결과 대비 품질이 악화되었는지 확인한다.

---

## 2. 주요 구성

```text
harness/
├── datasets/
│   ├── golden_ja_ko.jsonl
│   └── smoke_cases.jsonl
├── prompts/
│   ├── translate_ja_ko_v1.md
│   └── translate_v2.md
├── evaluators/
│   ├── rule_checks.py
│   ├── consistency.py
│   └── regression.py
├── reports/
└── run_eval.py
```

---

## 3. 검증 항목

```text
일본어 잔존 여부
문단 수 유지 여부
대사 따옴표 유지 여부
고유명사 보존 여부
용어집 준수 여부
번역 누락 여부
과도한 요약 여부
말투 일관성
존댓말/반말 보존
모델 응답 시간
chunk 병합 안정성
프롬프트 변경 전후 품질 차이
```

---

## 4. Golden Dataset 형식

파일 위치:

```text
harness/datasets/golden_ja_ko.jsonl
```

예시:

```jsonl
{"id":"case_001","source":"彼は静かに笑った。","reference":"그는 조용히 웃었다.","tags":["narration","short"]}
{"id":"case_002","source":"「あなたは誰ですか？」","reference":"“당신은 누구세요?”","tags":["dialogue","honorific"]}
{"id":"case_003","source":"魔王は王都の空を見上げた。","reference":"마왕은 왕도의 하늘을 올려다보았다.","tags":["glossary","fantasy"]}
```

---

## 5. 통과 기준

```text
no_japanese_left_score >= 0.98
paragraph_match_score >= 0.95
glossary_preserve_score >= 0.95
dialogue_style_score >= 0.90
no_empty_translation_score = 1.00
```

응답 시간 기준은 로컬 머신 성능에 따라 조정할 수 있다.

---

## 6. 평가 결과 저장

평가 결과는 파일과 DB에 모두 저장한다.

파일 저장 위치:

```text
harness/reports/
```

DB 저장 테이블:

```text
eval_runs
eval_results
```

DB 구조의 세부 기준은 `Docs/DB.md`를 따른다.

---

## 7. 프롬프트 변경 시 절차

```text
1. 새 prompt 파일 작성
2. prompt_versions에 버전 기록
3. smoke dataset 실행
4. golden dataset regression 실행
5. reports에 결과 저장
6. eval_runs / eval_results 저장
7. 악화 케이스 분석
8. 품질 개선이면 기본 PROMPT_VERSION 갱신
```

---

## 8. 실행 명령

### 8.1 Smoke Test

```bash
python harness/run_eval.py \
  --dataset harness/datasets/smoke_cases.jsonl \
  --prompt harness/prompts/translate_ja_ko_v1.md \
  --model gemma4:26b-a4b-it-q4_K_M
```

### 8.2 Regression Test

```bash
python harness/run_eval.py \
  --dataset harness/datasets/golden_ja_ko.jsonl \
  --prompt harness/prompts/translate_ja_ko_v1.md \
  --model gemma4:26b-a4b-it-q4_K_M \
  --output harness/reports/latest.json
```
