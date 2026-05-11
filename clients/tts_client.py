"""TTS / Text-to-Speech client."""

import httpx
import time
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio_bytes: bytes
    output_path: Path | None
    content_type: str


class TTSClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 120):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = 3
        self.retry_backoff_seconds = 1.0

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code in {408, 425, 429, 500, 502, 503, 504}

    def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: str = "Rajesh",
        model: str = "zero-indic",
        response_format: str = "wav",
        output_path: str | Path | None = None,
    ) -> TTSResult:
        """Convert text to speech audio."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": text,
            "voice": voice,
            "model": model,
            "language": language,
            "response_format": response_format,
        }
        last_error: Exception | None = None
        resp = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = httpx.post(
                    f"{self.base_url}/v1/audio/speech",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code if e.response is not None else None
                can_retry = bool(status and self._is_retryable_status(status))
                if can_retry and attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds * attempt)
                    continue
                raise
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_backoff_seconds * attempt)
                    continue
                raise RuntimeError(f"TTS transient failure after retries: {e}") from e

        if resp is None:
            raise RuntimeError(f"TTS call failed: {last_error}")

        saved_path = None
        if output_path:
            saved_path = Path(output_path)
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            saved_path.write_bytes(resp.content)

        return TTSResult(
            audio_bytes=resp.content,
            output_path=saved_path,
            content_type=resp.headers.get("content-type", ""),
        )
