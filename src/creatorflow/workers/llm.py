import json
import logging
from dataclasses import dataclass
import ollama
from creatorflow.config import settings
from creatorflow.workers.transcriber import Segment

logger = logging.getLogger(__name__)


@dataclass
class TimeRange:
    start:  float
    end:    float
    reason: str = ""


@dataclass
class EditPlan:
    keep_segments:       list[TimeRange]
    cut_segments:        list[TimeRange]
    total_kept_duration: float


@dataclass
class QualityReport:
    overall_score:    int
    pacing_score:     int
    clarity_score:    int
    filler_word_count:int
    filler_words:     list[str]
    retake_count:     int
    feedback:         str
    recommendations:  list[str]


# ── prompts ──────────────────────────────────────────────────────────────────

_EDIT_SYS = """\
You are a short-form video editor. Identify: PAUSES (silences >0.8s), RETAKES (repeated sentences), \
FILLER (um/uh/basically/you know). Return ONLY valid JSON: \
{"keep":[{"start":float,"end":float,"reason":"string"}],"cut":[...]} No markdown."""

_QUALITY_SYS = """\
You are a content coach. Analyse the transcript. Return ONLY valid JSON: \
{"overall_score":int,"pacing_score":int,"clarity_score":int,"filler_word_count":int,\
"filler_words":["list"],"retake_count":int,"feedback":"string","recommendations":["tip1","tip2"]} No markdown."""

_CAPTION_SYS = """\
You are a social media copywriter for Indian creators. Write 3 hook-first captions under 150 chars each \
with 3-5 hashtags. Return ONLY a JSON array of 3 strings. No markdown."""


# ── public API ────────────────────────────────────────────────────────────────

def plan_edits(segments: list[Segment], duration: float) -> EditPlan:
    body = f"Duration: {duration:.1f}s\nTranscript:\n{_fmt(segments)}\nAccount for every second in keep or cut."
    data = _chat(_EDIT_SYS, body, temp=0.1)
    keep = [TimeRange(r["start"], r["end"], r.get("reason","")) for r in data.get("keep", [])]
    cut  = [TimeRange(r["start"], r["end"], r.get("reason","")) for r in data.get("cut",  [])]
    logger.info(f"[llm] edit plan: {len(keep)} keep, {len(cut)} cut")
    return EditPlan(keep, cut, sum(r.end - r.start for r in keep))


def generate_quality_report(segments: list[Segment]) -> QualityReport:
    data = _chat(_QUALITY_SYS, f"Transcript:\n{_fmt(segments)}", temp=0.3)
    return QualityReport(**data)


def generate_captions(segments: list[Segment]) -> list[str]:
    hook = [s for s in segments if s.start < 30]
    data = _chat(_CAPTION_SYS, f"First 30s transcript:\n{_fmt(hook)}", temp=0.7)
    return data if isinstance(data, list) else [str(data)]


# ── helpers ───────────────────────────────────────────────────────────────────

def _fmt(segments: list[Segment]) -> str:
    return "\n".join(f"[{s.start:.2f}s-{s.end:.2f}s] {s.text}" for s in segments)


def _chat(system: str, user: str, temp: float) -> dict | list:
    resp = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        options={"temperature": temp},
    )
    raw = resp["message"]["content"].strip()
    return _parse(raw)


def _parse(raw: str) -> dict | list:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"[llm] json parse failed: {e}\nraw={raw[:300]}")
            raise ValueError("LLM returned invalid JSON") from e
