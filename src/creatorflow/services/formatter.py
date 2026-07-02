"""
Converts the raw quality_report dict produced by workers/llm.py
into plain-English strings suitable for non-technical creators.
All methods are pure functions — no I/O.
"""
from dataclasses import dataclass
from creatorflow.db.models.user import CreatorProfile
from creatorflow.services.profiles import get as get_profile_config


@dataclass
class FormattedReport:
    stars:        str          # e.g. "⭐⭐⭐⭐⭐⭐⭐☆☆☆"
    score:        int
    level:        str          # "Good", "Excellent", etc.
    summary:      str          # one sentence
    strengths:    list[str]
    improvements: list[str]
    tips:         list[str]


def format_report(qr: dict, profile: CreatorProfile) -> FormattedReport:
    score = int(qr.get("overall_score") or 0)
    level, summary = _level(score)
    return FormattedReport(
        stars=_stars(score),
        score=score,
        level=level,
        summary=summary,
        strengths=_strengths(qr),
        improvements=_improvements(qr),
        tips=list(get_profile_config(profile).tips),
    )


def explain_filler(qr: dict) -> dict:
    count = qr.get("filler_word_count", 0)
    words = qr.get("filler_words", [])
    return {
        "count": count,
        "words": words,
        "what_it_is": (
            "Filler words are the little sounds we make while thinking — "
            "'um', 'uh', 'like', 'basically'. Totally normal, but fewer = more polished."
        ),
        "what_we_did": "The AI removed the pauses around them. Your video already sounds smooth.",
        "tip": "Next time: pause and breathe instead of saying 'um'. That pause actually sounds confident.",
        "is_serious": count > 20,
    }


def explain_retakes(qr: dict) -> dict:
    count = qr.get("retake_count", 0)
    return {
        "count": count,
        "what_it_is": (
            "A retake is when you stopped and restarted a sentence mid-recording to get it right. "
            "Completely normal — it shows you care about quality."
        ),
        "what_we_did": f"We detected {count} restart{'s' if count != 1 else ''} and smoothed them out. "
                       "Your video flows without any awkward jumps.",
        "tip": "To reduce retakes: do one quick practice run before recording.",
        "is_serious": count > 5,
    }


def explain_pacing(qr: dict) -> dict:
    score = int(qr.get("pacing_score") or 0)
    if score >= 8:
        meaning = "Excellent pacing — viewers will stay engaged the whole time."
        tip = "Keep doing what you're doing."
    elif score >= 6:
        meaning = "Good pacing overall, with a few slow stretches."
        tip = "Try speaking a bit faster during explanations, and cut pauses longer than 2 seconds."
    elif score >= 4:
        meaning = "Some parts feel slow — viewers may click away before the end."
        tip = "Remove long silences, pick up the energy, and keep sentences shorter."
    else:
        meaning = "The pacing is quite slow throughout."
        tip = "Practice delivering your content faster. Think 'exciting news anchor', not 'bedtime story'."
    return {"score": score, "meaning": meaning, "tip": tip}


def explain_clarity(qr: dict) -> dict:
    score = int(qr.get("clarity_score") or 0)
    if score >= 8:
        meaning = "Crystal clear — people can understand every word without subtitles."
    elif score >= 6:
        meaning = "Mostly clear. A few moments are hard to follow."
    else:
        meaning = "Hard to understand in places. Viewers may turn on subtitles or give up."
    tip = "Record in a quiet room and speak directly at your microphone or phone speaker." if score < 8 else ""
    return {"score": score, "meaning": meaning, "tip": tip}


# ── private helpers ──────────────────────────────────────────────────────────

def _stars(score: int) -> str:
    s = max(0, min(10, score))
    return "⭐" * s + "☆" * (10 - s)


def _level(score: int) -> tuple[str, str]:
    if score >= 9: return "Excellent",  "This is professional-level content. People will love it."
    if score >= 7: return "Good",       "Most viewers will enjoy this. A few small tweaks could make it even better."
    if score >= 5: return "OK",         "Watchable, but some improvements would help it perform better."
    if score >= 3: return "Rough",      "This needs work before posting. See the suggestions below."
    return                "Redo",       "We recommend recording this one again. Check the tips below."


def _strengths(qr: dict) -> list[str]:
    out = []
    if (qr.get("clarity_score") or 0) >= 8:
        out.append("✓ Your voice is crystal clear and easy to understand")
    if (qr.get("pacing_score") or 0) >= 7:
        out.append("✓ Great pacing — viewers won't get bored")
    if (qr.get("filler_word_count") or 0) < 5:
        out.append("✓ Almost no filler words — sounds very professional")
    if (qr.get("retake_count") or 0) == 0:
        out.append("✓ Smooth delivery from start to finish")
    if not out:
        out.append("✓ You showed up and recorded — that's the hardest part")
    return out


def _improvements(qr: dict) -> list[str]:
    out = []
    if (qr.get("pacing_score") or 0) < 6:
        out.append("Pacing — some parts feel slow. Try speaking a little faster.")
    if (qr.get("filler_word_count") or 0) > 10:
        count = qr["filler_word_count"]
        out.append(f"Filler words — you said 'um' or 'like' {count} times. Try pausing instead.")
    if (qr.get("retake_count") or 0) > 3:
        out.append("Restarts — practice your points once before recording to reduce re-takes.")
    if (qr.get("clarity_score") or 0) < 6:
        out.append("Audio clarity — try recording in a quieter spot or closer to your mic.")
    return out
