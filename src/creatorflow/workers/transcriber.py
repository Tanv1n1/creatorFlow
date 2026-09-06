import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from groq import Groq
from creatorflow.config import settings

logger = logging.getLogger(__name__)
_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


@dataclass
class Segment:
    start: float
    end:   float
    text:  str


@dataclass
class TranscriptResult:
    source_segments:      list[Segment]
    english_segments:     list[Segment]
    detected_language:    str
    language_probability: float


def transcribe(video_path: str) -> TranscriptResult:
    """Transcribes (source language) and translates (to English) via Groq's hosted Whisper API."""
    audio_path = _extract_audio(video_path)
    try:
        client = _get_client()

        logger.info(f"[transcriber] transcribing {video_path} via Groq ({settings.groq_whisper_model})")
        raw_src = client.audio.transcriptions.create(
            file=(Path(audio_path).name, Path(audio_path).read_bytes()),
            model=settings.groq_whisper_model,
            response_format="verbose_json",
        )
        src = [Segment(_f(s, "start"), _f(s, "end"), _f(s, "text").strip())
               for s in _f(raw_src, "segments") if _f(s, "text").strip()]
        detected_language = _f(raw_src, "language") or "en"

        logger.info("[transcriber] translating to english via Groq")
        raw_eng = client.audio.translations.create(
            file=(Path(audio_path).name, Path(audio_path).read_bytes()),
            model=settings.groq_whisper_model,
            response_format="verbose_json",
        )
        eng = [Segment(_f(s, "start"), _f(s, "end"), _f(s, "text").strip())
               for s in _f(raw_eng, "segments") if _f(s, "text").strip()]

        logger.info(f"[transcriber] done — lang={detected_language}, {len(src)} src segs, {len(eng)} eng segs")
        return TranscriptResult(src, eng, detected_language, 1.0)
    finally:
        Path(audio_path).unlink(missing_ok=True)


def _f(obj, key):
    """Groq's verbose_json segments come back as plain dicts; the top-level response is an object."""
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _extract_audio(video_path: str) -> str:
    """Pulls a small mono audio track so we upload far less data than the raw video."""
    out = tempfile.mktemp(suffix=".mp3")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", out],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed (code {r.returncode}): {r.stderr[-500:]}")
    return out


def segments_to_srt(segments: list[Segment]) -> str:
    lines = []
    for i, s in enumerate(segments, 1):
        lines += [str(i), f"{_ts(s.start)} --> {_ts(s.end)}", s.text, ""]
    return "\n".join(lines)


def _ts(sec: float) -> str:
    h, rem = divmod(int(sec), 3600)
    m, s   = divmod(rem, 60)
    ms     = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
