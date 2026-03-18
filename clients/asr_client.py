"""ASR / Speech-to-Text client."""

import httpx
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ASRResult:
    text: str
    language: str
    duration: float | None
    raw: dict


class ASRClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 120):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def transcribe(
        self,
        audio_path: str | Path,
        language_code: str = "Hindi",
        model: str = "zero-indic",
        response_format: str = "verbose_json",
        use_vad_chunking: bool = True,
        enable_profanity_hashing: bool = False,
    ) -> ASRResult:
        """Transcribe an audio file using the ASR endpoint."""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        mime = "audio/wav" if audio_path.suffix in (".wav", ".wave") else f"audio/{audio_path.suffix.lstrip('.')}"

        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, mime)}
            data = {
                "enable_profanity_hashing": str(enable_profanity_hashing).lower(),
                "task": "transcribe",
                "model": model,
                "use_vad_chunking": str(use_vad_chunking).lower(),
                "language_code": language_code,
                "response_format": response_format,
            }
            headers = {
                "accept": "application/json",
                "api-key": self.api_key,
            }

            resp = httpx.post(
                f"{self.base_url}/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files,
                timeout=self.timeout,
            )

        resp.raise_for_status()
        body = resp.json()

        return ASRResult(
            text=body.get("text", ""),
            language=body.get("language", language_code),
            duration=body.get("duration"),
            raw=body,
        )
