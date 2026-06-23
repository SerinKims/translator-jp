from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from app.crawler.pixiv_client import (
    PixivAccessDeniedError,
    PixivClientError,
    PixivHttpClient,
)
from app.crawler.pixiv_parser import PixivParseError, parse_pixiv_novel_html
from app.crawler.pixiv_types import PixivFetchedPage
from app.crawler.url_validator import UnsupportedPixivUrlError, validate_pixiv_novel_url
from app.db.repositories.translation_repository import TranslationRepository
from app.schemas.fetch import PixivFetchResponse


class PixivClientProtocol(Protocol):
    async def fetch_html(self, url: str) -> PixivFetchedPage:
        ...

    async def fetch_novel_json(self, source_url: str, source_work_id: str) -> PixivFetchedPage:
        ...


class FetchServiceError(RuntimeError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FetchService:
    def __init__(
        self,
        db: Session,
        *,
        pixiv_client: PixivClientProtocol | None = None,
    ) -> None:
        self.db = db
        self.pixiv_client = pixiv_client or PixivHttpClient()
        self.translation_repository = TranslationRepository(db)

    async def fetch_pixiv(
        self,
        *,
        url: str,
        translate_after_fetch: bool = False,
    ) -> PixivFetchResponse:
        try:
            source = validate_pixiv_novel_url(url)
        except UnsupportedPixivUrlError as exc:
            raise FetchServiceError(str(exc), status_code=400) from exc

        try:
            page = await self.pixiv_client.fetch_html(source["source_url"])
            novel = parse_pixiv_novel_html(page.html, source["source_url"])
        except PixivAccessDeniedError as exc:
            raise FetchServiceError(exc.message, status_code=exc.status_code) from exc
        except PixivClientError as exc:
            raise FetchServiceError(exc.message, status_code=exc.status_code) from exc
        except PixivParseError as exc:
            try:
                page = await self.pixiv_client.fetch_novel_json(
                    source["source_url"],
                    source["source_work_id"],
                )
                novel = parse_pixiv_novel_html(page.html, source["source_url"])
            except PixivAccessDeniedError as ajax_exc:
                raise FetchServiceError(
                    ajax_exc.message,
                    status_code=ajax_exc.status_code,
                ) from ajax_exc
            except PixivClientError as ajax_exc:
                raise FetchServiceError(
                    ajax_exc.message,
                    status_code=ajax_exc.status_code,
                ) from ajax_exc
            except PixivParseError:
                raise FetchServiceError(exc.message, status_code=422) from exc

        status = "pending_translation" if translate_after_fetch else "fetched"
        job = self.translation_repository.create_job(
            source_site="pixiv",
            source_url=novel.source_url,
            source_title=novel.title,
            source_author=novel.author,
            source_work_id=novel.source_work_id,
            source_fetched_at=datetime.now(timezone.utc),
            original_text=novel.text,
            status=status,
        )

        return PixivFetchResponse(
            source_site=novel.source_site,
            source_url=novel.source_url,
            source_work_id=novel.source_work_id,
            title=novel.title,
            author=novel.author,
            text=novel.text,
            char_count=novel.char_count,
            job_id=job.id,
        )
