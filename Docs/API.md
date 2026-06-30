# API Specification

## 2026-06-30 Page Translation Contract

When `text` contains `[newpage]`, translation is page-scoped.

- `POST /api/translate` defaults to `translate_scope=first_page` and `page_index=0`.
- Supported `translate_scope` values are `first_page`, `current_page`, and `all_pages`.
- `first_page` translates only page `0`.
- `current_page` translates only the supplied `page_index`.
- `all_pages` translates every page only when explicitly requested.
- Completed pages are reused from `translation_pages` before checking cache or calling the LLM.
- Response fields include `current_page_index`, `total_pages`, and `has_next_page`.

Additional endpoint:

```http
POST /api/translations/{job_id}/pages/{page_index}/translate
```

This endpoint translates or retries one selected page and returns the same
`TranslationResponse` shape as `POST /api/translate`.

## 1. 공통 원칙

- API route는 request/response schema를 명확히 정의한다.
- 사용자에게 노출되는 오류 메시지는 이해 가능한 한국어로 반환한다.
- 내부 로그에는 오류 코드와 metadata를 남기되 긴 원문 전체를 저장하지 않는다.
- DB 접근은 repository layer를 통해 수행한다.

---

## 2. Health Check

```http
GET /api/health
```

역할:

```text
Backend 정상 여부 확인
Ollama 사용 가능 여부 확인
gemma4:26b-a4b-it-q4_K_M 모델 사용 가능 여부 확인
DB 연결 여부 확인
```

Response:

```json
{
  "status": "ok",
  "ollama": "ok",
  "database": "ok",
  "model": "gemma4:26b-a4b-it-q4_K_M"
}
```

---

## 3. Pixiv 원문 수집

```http
POST /api/fetch/pixiv
```

Request:

```json
{
  "url": "https://www.pixiv.net/novel/show.php?id=12345678",
  "translate_after_fetch": false
}
```

Response:

```json
{
  "source_site": "pixiv",
  "source_url": "https://www.pixiv.net/novel/show.php?id=12345678",
  "source_work_id": "12345678",
  "title": "作品タイトル",
  "author": "作者名",
  "text": "小説本文...",
  "char_count": 12000,
  "job_id": 1
}
```

---

## 4. Pixiv 수집 후 즉시 번역

```http
POST /api/fetch/pixiv/translate
```

Request:

```json
{
  "url": "https://www.pixiv.net/novel/show.php?id=12345678",
  "source_lang": "ja",
  "target_lang": "ko",
  "style": "webnovel",
  "honorific_policy": "preserve",
  "preserve_names": true,
  "use_glossary": true,
  "use_cache": true,
  "think": "low",
  "options": {
    "temperature": 0.2,
    "max_tokens": 2048
  }
}
```

Response:

```json
{
  "job_id": 1,
  "source_site": "pixiv",
  "source_url": "https://www.pixiv.net/novel/show.php?id=12345678",
  "source_work_id": "12345678",
  "title": "作品タイトル",
  "author": "作者名",
  "translated_text": "한국어 번역문...",
  "model": "gemma4:26b-a4b-it-q4_K_M",
  "prompt_version": "translate_ja_ko_v1",
  "elapsed_ms": 1234,
  "chunks": [
    {
      "index": 0,
      "source_lang": "ja",
      "target_lang": "ko",
      "status": "completed"
    }
  ]
}
```

동작:

```text
pixiv 단건 URL을 Backend에서 수집한다.
수집한 원문과 pixiv source metadata로 translation_jobs를 생성한다.
TranslationService의 공통 chunk 번역 로직으로 같은 job_id를 번역한다.
chunk 상태와 최종 번역문은 manual job이 아니라 pixiv job에 저장한다.
```

---

## 5. 직접 원문 번역 요청

```http
POST /api/translate
```

MVP implementation contract:

```json
{
  "text": "貼り付けた日本語の原文...",
  "source_lang": "ja",
  "target_lang": "ko",
  "translate_scope": "first_page",
  "page_index": 0,
  "style": "webnovel",
  "honorific_policy": "preserve",
  "preserve_names": true,
  "use_glossary": true,
  "use_cache": true,
  "stream": false,
  "think": false,
  "options": null
}
```

Defaults are `source_lang=ja`, `target_lang=ko`, `translate_scope=first_page`,
`page_index=0`, `style=webnovel`, `honorific_policy=preserve`,
`preserve_names=true`, `use_glossary=true`, `use_cache=true`, and `stream=false`.
`stream=true` is not supported in the MVP.

The response includes pasted-text metadata:

```json
{
  "job_id": 1,
  "source_type": "pasted_text",
  "source_lang": "ja",
  "target_lang": "ko",
  "current_page_index": 0,
  "total_pages": 1,
  "has_next_page": false,
  "translated_text": "한국어 번역문...",
  "model": "gemma4:26b-a4b-it-q4_K_M",
  "prompt_version": "translate_ja_ko_v1",
  "style": "webnovel",
  "elapsed_ms": 1234,
  "cache_hit": false,
  "chunks": [
    {
      "index": 0,
      "source_lang": "ja",
      "target_lang": "ko",
      "status": "completed"
    }
  ]
}
```

Request:

```json
{
  "text": "日本語の原文",
  "style": "webnovel",
  "honorific_policy": "preserve",
  "preserve_names": true,
  "use_glossary": true,
  "use_cache": true,
  "stream": false,
  "think": false,
  "options": {
    "temperature": 0.2,
    "max_tokens": 2048
  }
}
```

Response:

```json
{
  "job_id": 1,
  "translated_text": "한국어 번역문",
  "model": "gemma4:26b-a4b-it-q4_K_M",
  "prompt_version": "translate_ja_ko_v1",
  "style": "webnovel",
  "elapsed_ms": 1234,
  "cache_hit": false,
  "chunks": [
    {
      "index": 0,
      "source": "日本語の原文",
      "translation": "한국어 번역문",
      "status": "completed"
    }
  ]
}
```

---

## 6. 번역 이력

### 6.1 목록 조회

```http
GET /api/translations
```

### 6.2 상세 조회

```http
GET /api/translations/{job_id}
```

### 6.3 chunk 재시도

```http
POST /api/translations/{job_id}/chunks/{chunk_index}/retry
```

---

## 7. 용어집

### 7.1 용어집 조회

```http
GET /api/glossary
```

### 7.2 용어집 추가

```http
POST /api/glossary
```

Request:

```json
{
  "source_lang": "ja",
  "target_lang": "ko",
  "source_term": "王都",
  "target_term": "왕도",
  "term_type": "place",
  "description": "판타지 문맥에서 수도보다 자연스러운 번역",
  "aliases": ["王城", "王国の都"],
  "priority": 80,
  "is_required": true,
  "is_active": true
}
```

Response:

```json
{
  "id": 1,
  "source_lang": "ja",
  "target_lang": "ko",
  "source_term": "王都",
  "target_term": "왕도",
  "term_type": "place",
  "description": "판타지 문맥에서 수도보다 자연스러운 번역",
  "aliases": ["王城", "王国の都"],
  "priority": 80,
  "is_required": true,
  "is_active": true,
  "created_at": "2026-06-26T10:00:00",
  "updated_at": "2026-06-26T10:00:00"
}
```

`GET /api/glossary`는 위 응답 객체의 배열을 반환한다.

### 7.3 용어집 수정

```http
PATCH /api/glossary/{term_id}
```

Request는 `POST /api/glossary`와 같은 필드의 부분 집합을 받는다. `is_active=true`로 PATCH하면 비활성 용어를 재활성화할 수 있다.

정책:

```text
같은 source_lang + target_lang + source_term + target_term 조합은 중복 추가하지 않는다.
같은 source_lang + target_lang + source_term에 다른 target_term이 있으면 409 Conflict를 반환한다.
비활성 용어 재활성화는 POST가 아니라 PATCH로 처리한다.
```

### 7.4 용어집 비활성화

```http
DELETE /api/glossary/{term_id}
```

실제 row를 삭제하지 않고 `is_active=false`로 변경한다. 응답은 변경된 용어 객체를 반환한다.

### 7.5 CSV import

```http
POST /api/glossary/import
```

본문은 raw CSV 또는 JSON `{ "text": "..." }`를 지원한다.

CSV 형식:

```csv
source_lang,target_lang,source_term,target_term,term_type,priority,is_required,description,aliases
ja,ko,王都,왕도,place,80,true,판타지 문맥에서는 수도보다 왕도가 자연스러움,"王城|王国の都"
```

Response:

```json
{
  "imported": 2,
  "skipped_duplicates": 1,
  "conflicts": [
    {
      "row": 4,
      "source_lang": "ja",
      "target_lang": "ko",
      "source_term": "王都",
      "target_term": "수도",
      "message": "같은 원어에 다른 번역어가 이미 등록되어 있습니다."
    }
  ]
}
```

### 7.6 후보 용어

```http
GET /api/glossary/candidates
POST /api/glossary/candidates/{candidate_id}/approve
POST /api/glossary/candidates/{candidate_id}/reject
```

후보 상태는 `pending`, `approved`, `rejected`만 허용한다.

Approve는 후보를 `glossary_terms`에 등록하고 후보 상태를 `approved`로 바꾸는 작업을 한 트랜잭션으로 처리한다. 등록 중 duplicate/conflict가 발생하면 409를 반환하고 후보는 `pending`으로 남는다. Reject는 용어를 등록하지 않고 후보 상태만 `rejected`로 변경한다.

---

## 8. 피드백 저장

```http
POST /api/feedback
```

Request:

```json
{
  "job_id": 1,
  "chunk_id": 3,
  "source_text": "王都の空を見上げた。",
  "model_translation": "수도의 하늘을 올려다보았다.",
  "user_corrected_translation": "왕도의 하늘을 올려다보았다.",
  "rating": 3,
  "feedback_type": "glossary_violation",
  "comment": "王都는 왕도로 번역해야 함"
}
```
