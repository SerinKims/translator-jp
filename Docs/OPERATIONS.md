# OPERATIONS

## 1. Health Check

`GET /api/health`는 다음 상태를 확인한다.

```text
Backend 정상 여부
LiteRT-LM 사용 가능 여부
gemma4-e4b 모델 파일 사용 가능 여부
DB 연결 여부
```

---

## 2. 오류 처리 정책

| 상황 | 사용자 메시지 | 로그 코드 |
|---|---|---|
| Pixiv URL 오류 | 지원하지 않는 pixiv URL입니다. 소설 상세 페이지 URL을 입력해주세요. | `PIXIV_INVALID_URL` |
| Pixiv 수집 실패 | pixiv 원문을 가져오지 못했습니다. URL을 확인하거나 원문을 직접 입력해주세요. | `PIXIV_FETCH_FAILED` |
| Pixiv 접근 제한 | 해당 pixiv 페이지에 접근할 수 없습니다. 브라우저에서 열람 가능한 페이지인지 확인해주세요. | `PIXIV_ACCESS_DENIED` |
| Pixiv 원문 추출 실패 | 페이지는 열렸지만 소설 원문을 찾지 못했습니다. 원문을 직접 입력해주세요. | `PIXIV_PARSE_FAILED` |
| LiteRT-LM 사용 불가 | LiteRT-LM을 사용할 수 없습니다. backend requirements와 로컬 모델 파일을 확인해주세요. | `LITERT_LM_RUNTIME_ERROR` |
| 모델 파일 없음 | gemma4-e4b 모델 파일을 찾을 수 없습니다. LITERT_LM_MODEL_PATH가 올바른지 확인해주세요. | `LITERT_LM_MODEL_NOT_FOUND` |
| Timeout | 번역 시간이 너무 오래 걸렸습니다. 입력 문장을 줄이거나 다시 시도해주세요. | `LITERT_LM_TIMEOUT` |
| Empty Response | 모델이 빈 응답을 반환했습니다. 다시 시도해주세요. | `EMPTY_MODEL_RESPONSE` |
| DB Error | 번역 결과 저장 중 문제가 발생했습니다. 다시 시도해주세요. | `DATABASE_ERROR` |

---

## 3. 로깅 원칙

- 오류 코드는 반드시 남긴다.
- 응답 시간, chunk index, job id, prompt version, model name은 추적 가능해야 한다.
- 긴 원문 전체를 로그에 남기지 않는다.
- 원문이 필요한 경우 짧은 preview와 char count만 남긴다.
- raw_model_response 저장 여부는 환경 변수로 제어한다.

---

## 4. 성능 최적화 방향

우선순위:

```text
1. pixiv URL 단위 fetch cache 적용
2. chunk 크기 최적화
3. translation_cache 적용
4. streaming 응답 적용
5. prompt 길이 축소
6. glossary context 최소화
7. 동일 입력 cache hit 개선
8. 긴 텍스트 진행 상태 표시
9. 실패 chunk만 재시도
```

---

## 5. Mac M1 환경 최적화

Mac M1 환경에서는 다음을 우선 적용한다.

```text
LiteRT-LM 로컬 모델 파일 확인
num_ctx를 과도하게 크게 설정하지 않기
긴 소설은 문단 단위로 나누어 번역
프롬프트를 짧고 명확하게 유지
전체 완료 후 표시보다 chunk별 진행 표시 사용
```
