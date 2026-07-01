# LLM / Prompt / Chunking 정책

## 2026-06-30 Page-Aware Chunking

Before chunking, source text is split on `[newpage]`.

- Empty pages are removed.
- Page indexes start at `0`.
- Text without `[newpage]` is treated as one page.
- `TranslationService` chunks only the selected page's `source_text`.
- The service must not always chunk `translation_jobs.original_text`.
- Completed pages in `translation_pages` are reused before cache lookup or LLM calls.
- Existing chunking, glossary, and cache logic still run below the selected page.

Translate scope:

- `first_page`: translate page `0`.
- `current_page`: translate the requested `page_index`.
- `all_pages`: translate all pages only when explicitly requested.

## 1. 기본 Runtime

```text
LLM Runtime: Ollama
Model: gemma4:26b-a4b-it-q4_K_M
Model source: local Ollama model registry
API: ollama.chat Python API
```

Backend에서만 Ollama를 호출한다. Frontend에서 Ollama를 직접 호출하지 않는다.

---

## 2. Ollama Client

파일:

```text
backend/app/llm/ollama_client.py
```

책임:

```text
ollama.chat 호출
timeout 처리
에러 응답 정규화
모델명 주입
응답 시간 측정
```

비즈니스 로직은 넣지 않는다.

Ollama 호출 옵션:

```text
think: str 또는 bool
options: dict
```

`think`와 `options`는 사용자 요청 또는 호출자가 직접 지정할 수 있다. `think` 기본값은 `False`이고, `options`를 지정하지 않으면 Ollama 기본값을 사용하도록 `None`으로 전달한다.

---

## 3. Translator Service

파일:

```text
backend/app/llm/translator.py
```

책임:

```text
프롬프트 구성
chunk별 번역 호출
glossary 적용
cache 확인
번역 결과 병합
실패 chunk 재시도
결과 metadata 생성
translation_jobs 업데이트
translation_chunks 업데이트
```

---

## 4. 기본 번역 프롬프트

프롬프트는 코드에 직접 하드코딩하지 않는다.

프롬프트 파일 위치:

```text
harness/prompts/
```

기본 프롬프트:

```text
harness/prompts/translate_ja_ko_v1.md
```

기본 내용:

```text
당신은 일본어 소설을 한국어 웹소설 문체로 번역하는 전문 번역가입니다.

목표:
- 일본어 원문의 의미를 보존합니다.
- 한국어 독자가 자연스럽게 읽을 수 있도록 번역합니다.
- 대사, 독백, 설명문을 구분합니다.
- 문단 수와 순서를 최대한 유지합니다.
- 고유명사, 인명, 지명은 임의로 바꾸지 않습니다.
- 존댓말과 반말의 관계성을 보존합니다.
- 과도한 의역, 요약, 삭제를 하지 않습니다.
- 원문에 없는 설정을 추가하지 않습니다.

출력:
- 번역문만 출력합니다.
- 설명, 주석, 분석을 출력하지 않습니다.
```

---

## 5. 출력 정책

번역 API 응답에는 모델의 분석 과정이나 설명을 포함하지 않는다.

모델이 설명을 함께 출력한 경우 다음 중 하나로 처리한다.

```text
후처리로 설명 제거
또는 재요청
```

---

Literal Unicode escape output such as `\u4f5c\u54c1` is restored during
translation post-processing before saving `translated_text` or returning API
responses. `raw_model_response` keeps the original model output.

## 6. 프롬프트 버전 관리

프롬프트 변경 시 다음을 수행한다.

```text
1. prompt_versions에 버전 기록
2. harness smoke test 실행
3. golden dataset regression 실행
4. eval_runs / eval_results 저장
5. 결과가 악화되면 변경 취소 또는 보완
```

번역 결과는 반드시 어떤 prompt version에서 생성되었는지 추적 가능해야 한다.

---

## 7. Chunking 정책

긴 일본어 원문은 chunk 단위로 나누어 번역한다.

분할 우선순위:

```text
1. 빈 줄 기준 문단 분리
2. 대사 블록 기준 분리
3. 문장 단위 분리
4. 최대 글자 수 기준 분리
```

기본 설정:

```text
MAX_CHARS_PER_CHUNK=1800
CHUNK_OVERLAP_PARAGRAPHS=1
```

주의사항:

```text
대사 도중에 자르지 않는다.
따옴표가 열려 있으면 다음 문장까지 포함한다.
앞 chunk의 마지막 인물명, 말투, 용어를 다음 chunk context로 전달한다.
최종 병합 시 문단 순서를 보존한다.
각 chunk 상태는 translation_chunks에 저장한다.
```

---

## 8. Chunker

파일:

```text
backend/app/services/chunker.py
```

책임:

```text
문단 분리
chunk 생성
overlap context 생성
원문 순서 index 부여
```

Chunker는 LLM을 호출하면 안 된다.

---

## 9. Glossary

파일:

```text
backend/app/services/glossary.py
```

책임:

```text
활성 용어집 조회
source_text에 포함된 source_term 탐색
source_text에 포함된 alias 탐색
prompt에 넣을 glossary context 생성
번역 결과의 glossary 위반 여부 검사
```

예시:

```text
魔王 → 마왕
勇者 → 용사
王都 → 왕도
姫様 → 공주님
```

번역 요청 시 활성화된 glossary를 prompt에 반영한다.

정책:

```text
용어집 전체를 prompt에 넣지 않는다.
현재 chunk에 등장하는 source_term 또는 alias가 있는 항목만 선별한다.
source_lang과 target_lang이 요청 언어와 일치하는 항목만 사용한다.
is_active=false인 항목은 사용하지 않는다.
is_active=false인 항목은 prompt glossary context와 cache glossary hash에 포함하지 않는다.
MAX_GLOSSARY_TERMS_PER_CHUNK=30
MAX_GLOSSARY_CONTEXT_CHARS=1500
```

정렬 기준:

```text
1. is_required=true 우선
2. priority 높은 순
3. source_term 길이 긴 순
4. source_term 오름차순
```

Prompt 삽입 형식:

```text
[용어집 - 반드시 지킬 것]
魔王=마왕
王都=왕도
姫様=공주님
```

`use_glossary=false`이면 glossary context를 prompt에 포함하지 않는다.
캐시 키에 사용하는 glossary hash는 전체 용어집이 아니라 현재 chunk에 선별된 용어만 기준으로 생성한다.
비활성 용어는 선별 대상에서 제외하므로 용어를 비활성화해도 prompt와 glossary hash에 남지 않는다.

---

## 10. Translation Cache

파일:

```text
backend/app/services/cache.py
```

책임:

```text
cache key 생성
translation_cache 조회
cache hit_count 증가
새 번역 결과 저장
```

cache key 구성 요소:

```text
source_text
model_name
prompt_version
style
honorific_policy
preserve_names
glossary_hash
```

cache hit 시 모델을 호출하지 않고 저장된 번역 결과를 반환한다.
## 2026-07-01 Multilingual Prompt Selection

The translation service supports these source language pairs for MVP:

```text
ja -> ko
zh-CN -> ko
zh-TW -> ko
en -> ko
```

Prompt files:

```text
harness/prompts/translate_ja_ko_v1.md
harness/prompts/translate_zh_ko_v1.md
harness/prompts/translate_en_ko_v1.md
```

`zh-CN` and `zh-TW` share `translate_zh_ko_v1`. Prompt selection, glossary
lookup, cache key generation, and chunk persistence all use the resolved source
language. If `source_lang=auto`, language detection runs before prompt loading.

Unsupported target languages are rejected because MVP target language is only
Korean (`ko`).
