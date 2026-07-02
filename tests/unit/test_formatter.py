import pytest
from creatorflow.services import formatter
from creatorflow.db.models.user import CreatorProfile


def _qr(**kw):
    return {"overall_score": 7, "pacing_score": 6, "clarity_score": 8,
            "filler_word_count": 5, "filler_words": ["um"], "retake_count": 1, **kw}


def test_stars_length():
    r = formatter.format_report(_qr(overall_score=7), CreatorProfile.CREATOR)
    assert len([c for c in r.stars if c in "⭐☆"]) == 10


def test_level_excellent():
    r = formatter.format_report(_qr(overall_score=9), CreatorProfile.CREATOR)
    assert r.level == "Excellent"


def test_level_redo():
    r = formatter.format_report(_qr(overall_score=1), CreatorProfile.CREATOR)
    assert r.level == "Redo"


def test_strengths_clarity():
    r = formatter.format_report(_qr(clarity_score=9, filler_word_count=0, retake_count=0, pacing_score=8), CreatorProfile.CREATOR)
    assert any("clear" in s for s in r.strengths)


def test_improvement_filler():
    r = formatter.format_report(_qr(filler_word_count=25), CreatorProfile.CREATOR)
    assert any("filler" in i.lower() or "um" in i.lower() for i in r.improvements)


def test_profile_tips_coach():
    r = formatter.format_report(_qr(), CreatorProfile.COACH)
    assert len(r.tips) > 0


def test_explain_filler_count():
    fi = formatter.explain_filler(_qr(filler_word_count=30))
    assert fi["count"] == 30
    assert fi["is_serious"] is True


def test_explain_retakes_serious():
    ri = formatter.explain_retakes(_qr(retake_count=6))
    assert ri["is_serious"] is True
