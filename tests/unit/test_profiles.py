from creatorflow.db.models.user import CreatorProfile
from creatorflow.services.profiles import get, all_profiles


def test_all_profiles_defined():
    assert len(all_profiles()) == 4


def test_creator_aggressive():
    assert get(CreatorProfile.CREATOR).edit_aggressiveness == "aggressive"


def test_coach_conservative():
    assert get(CreatorProfile.COACH).edit_aggressiveness == "conservative"


def test_podcaster_minimal():
    assert get(CreatorProfile.PODCASTER).edit_aggressiveness == "minimal"


def test_each_profile_has_tips():
    for p in CreatorProfile:
        assert len(get(p).tips) > 0


def test_portrait_format_creator():
    assert get(CreatorProfile.CREATOR).output_format == "portrait"


def test_landscape_format_business():
    assert get(CreatorProfile.BUSINESS).output_format == "landscape"
