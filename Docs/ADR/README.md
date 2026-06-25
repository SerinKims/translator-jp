# ADR Index

Architecture Decision Record는 장기적으로 유지할 기술 결정을 기록한다.

| ADR | 결정 |
|---|---|
| `0001-use-local-ollama-qwen3-14b.md` | 기본 LLM Runtime으로 로컬 Ollama + qwen3:14b 사용, ADR 0005로 대체됨 |
| `0002-use-sqlite-and-repository-layer.md` | 초기 DB로 SQLite 사용, DB 접근은 repository layer로 제한 |
| `0003-backend-only-pixiv-fetch.md` | pixiv 수집은 Backend 단건 URL 기반으로만 수행 |
| `0004-prompt-versioning-and-harness.md` | 프롬프트 버전 관리와 하네스 회귀 평가를 필수화 |
| `0005-use-local-litert-lm-gemma4-e4b.md` | 기본 LLM Runtime으로 로컬 LiteRT-LM + gemma4-e4b 사용, ADR 0006으로 대체됨 |
| `0006-use-local-ollama-gemma4-26b.md` | 기본 LLM Runtime으로 로컬 Ollama + gemma4:26b-a4b-it-q4_K_M 사용 |
