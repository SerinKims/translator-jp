# API Specification

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
      "status": "completed"
    }
  ]
}
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
  "source_term": "王都",
  "target_term": "왕도",
  "term_type": "place",
  "description": "판타지 문맥에서 수도보다 자연스러운 번역"
}
```

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
