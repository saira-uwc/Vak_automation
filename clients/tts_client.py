"""TTS / Text-to-Speech client."""

import httpx
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

    def synthesize(
        self,
        text: str,
        voice: str = "Rajesh",
        model: str = "zero-indic",
        response_format: str = "wav",
        output_path: str | Path | None = None,
    ) -> TTSResult:
        """Convert text to speech audio."""
        resp = httpx.post(
            f"{self.base_url}/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": text,
                "voice": voice,
                "model": model,
                "response_format": response_format,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()

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
