from __future__ import annotations

import asyncio
import time
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import httpx

from app.core.config import Settings, get_settings
from app.crawler.pixiv_types import (
    PIXIV_ACCESS_DENIED_MESSAGE,
    PIXIV_FETCH_FAILED_MESSAGE,
    PixivFetchedPage,
)


class PixivClientError(RuntimeError):
    status_code = 502

    def __init__(self, message: str = PIXIV_FETCH_FAILED_MESSAGE) -> None:
        super().__init__(message)
        self.message = message


class PixivAccessDeniedError(PixivClientError):
    status_code = 403

    def __init__(self, message: str = PIXIV_ACCESS_DENIED_MESSAGE) -> None:
        super().__init__(message)


class PixivFetchFailedError(PixivClientError):
    status_code = 502


class PixivHttpClient:
    _rate_limit_lock = asyncio.Lock()
    _last_request_at = 0.0

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def fetch_html(self, url: str) -> PixivFetchedPage:
        return await self._fetch_url(url)

    async def fetch_novel_json(self, source_url: str, source_work_id: str) -> PixivFetchedPage:
        ajax_url = f"https://www.pixiv.net/ajax/novel/{quote(source_work_id)}?lang=ja"
        return await self._fetch_url(
            ajax_url,
            referer=source_url,
            accept="application/json,text/plain,*/*",
        )

    async def _fetch_url(
        self,
        url: str,
        *,
        referer: str | None = None,
        accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    ) -> PixivFetchedPage:
        timeout = httpx.Timeout(self.settings.pixiv_fetch_timeout_seconds)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; translator-jp/0.1; +https://localhost.localdomain)"
            ),
            "Accept": accept,
            "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
        }
        if referer is not None:
            headers["Referer"] = referer

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            last_error: Exception | None = None
            for attempt in range(self.settings.pixiv_fetch_max_retries + 1):
                await self._wait_for_rate_limit()
                try:
                    response = await client.get(url)
                except httpx.TimeoutException as exc:
                    last_error = exc
                    if attempt >= self.settings.pixiv_fetch_max_retries:
                        break
                    continue
                except httpx.HTTPError as exc:
                    last_error = exc
                    if attempt >= self.settings.pixiv_fetch_max_retries:
                        break
                    continue

                if response.status_code in {401, 403}:
                    raise PixivAccessDeniedError()

                if response.status_code == 429:
                    if attempt >= self.settings.pixiv_fetch_max_retries:
                        raise PixivFetchFailedError()
                    await self._wait_for_retry_after(response)
                    continue

                if 500 <= response.status_code < 600:
                    if attempt >= self.settings.pixiv_fetch_max_retries:
                        raise PixivFetchFailedError()
                    continue

                if response.status_code >= 400:
                    raise PixivFetchFailedError()

                return PixivFetchedPage(
                    url=str(response.url),
                    html=response.text,
                    status_code=response.status_code,
                )

        raise PixivFetchFailedError() from last_error

    async def fetch_html_with_playwright(self, url: str) -> PixivFetchedPage:
        # Placeholder for a future explicit renderer. It intentionally keeps
        # the same public boundary as the regular HTTP fetch path.
        return await self.fetch_html(url)

    async def _wait_for_rate_limit(self) -> None:
        min_interval = max(0.0, self.settings.pixiv_fetch_min_interval_seconds)
        async with self._rate_limit_lock:
            now = time.monotonic()
            sleep_for = self._last_request_at + min_interval - now
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            type(self)._last_request_at = time.monotonic()

    @staticmethod
    async def _wait_for_retry_after(response: httpx.Response) -> None:
        retry_after = response.headers.get("Retry-After")
        if retry_after is None:
            await asyncio.sleep(1)
            return

        try:
            seconds = float(retry_after)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
            except (TypeError, ValueError):
                seconds = 1.0
            else:
                seconds = max(1.0, retry_at.timestamp() - time.time())

        await asyncio.sleep(min(seconds, 30.0))
