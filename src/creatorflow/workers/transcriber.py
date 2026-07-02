import logging
from dataclasses import dataclass
from typing import Optional
from faster_whisper import WhisperModel
from creatorflow.config import settings

logger = logging.getLogger(__name__)
_model: Optional[WhisperModel] = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info(f"[transcriber] loading {settings.whisper_model}")
        _model = WhisperModel(settings.whisper_model, device=settings.whisper_device, compute_type=settings.whisper_compute_type)
        logger.info("[transcriber] model ready")
    return _model


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
    model = _get_model()
    vad = {"min_silence_duration_ms": 500}

    logger.info(f"[transcriber] transcribing {video_path}")
    raw_src, info = model.transcribe(video_path, task="transcribe", language=None, vad_filter=True, vad_parameters=vad, beam_size=5)
    src = [Segment(s.start, s.end, s.text.strip()) for s in raw_src if s.text.strip()]

    logger.info("[transcriber] translating to english")
    raw_eng, _ = model.transcribe(video_path, task="translate", language=info.language, vad_filter=True, vad_parameters=vad, beam_size=5)
    eng = [Segment(s.start, s.end, s.text.strip()) for s in raw_eng if s.text.strip()]

    logger.info(f"[transcriber] done — lang={info.language} ({info.language_probability:.0%}), {len(src)} src segs, {len(eng)} eng segs")
    return TranscriptResult(src, eng, info.language, info.language_probability)


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
