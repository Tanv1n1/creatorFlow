from dataclasses import dataclass
from creatorflow.db.models.user import CreatorProfile


@dataclass(frozen=True)
class ProfileConfig:
    name:                str
    emoji:               str
    description:         str
    min_duration:        int    # seconds
    max_duration:        int
    edit_aggressiveness: str    # "aggressive" | "moderate" | "conservative" | "minimal"
    output_format:       str    # "portrait" | "landscape" | "audio"
    recommended_score:   int    # minimum score considered "good"
    tips:                tuple[str, ...]


PROFILES: dict[CreatorProfile, ProfileConfig] = {
    CreatorProfile.CREATOR: ProfileConfig(
        name="Content Creator",
        emoji="📸",
        description="Instagram / TikTok / YouTube Shorts",
        min_duration=15,
        max_duration=90,
        edit_aggressiveness="aggressive",
        output_format="portrait",
        recommended_score=7,
        tips=(
            "Fast pacing = more views. The AI removes slow parts automatically.",
            "Use the first caption option — it's written to hook viewers in 3 seconds.",
            "Test all 3 thumbnail options. The one with the biggest expression wins.",
        ),
    ),
    CreatorProfile.COACH: ProfileConfig(
        name="Educator / Coach",
        emoji="📚",
        description="Courses, tutorials, webinars",
        min_duration=120,
        max_duration=600,
        edit_aggressiveness="conservative",
        output_format="landscape",
        recommended_score=6,
        tips=(
            "Clarity matters more than speed here — your audience wants to learn.",
            "Add timestamps to your description so students can navigate easily.",
            "Clear audio keeps people watching. Yours looks great!",
        ),
    ),
    CreatorProfile.PODCASTER: ProfileConfig(
        name="Podcaster",
        emoji="🎙️",
        description="Audio-focused, long-form",
        min_duration=300,
        max_duration=3600,
        edit_aggressiveness="minimal",
        output_format="audio",
        recommended_score=8,
        tips=(
            "Audio clarity is everything for podcasts. Use a microphone if possible.",
            "Your transcript is ready — paste it into your show notes for SEO.",
            "Filler words matter less in long-form. Don't stress about a few 'ums'.",
        ),
    ),
    CreatorProfile.BUSINESS: ProfileConfig(
        name="Business Videos",
        emoji="💼",
        description="Product demos, testimonials, explainers",
        min_duration=60,
        max_duration=300,
        edit_aggressiveness="moderate",
        output_format="landscape",
        recommended_score=8,
        tips=(
            "Professional tone throughout. The AI keeps your full message intact.",
            "Optimize for LinkedIn and YouTube — both favour clear, concise delivery.",
            "A quality score of 8+ signals this is ready for client-facing use.",
        ),
    ),
}


def get(profile: CreatorProfile) -> ProfileConfig:
    return PROFILES[profile]


def all_profiles() -> dict[CreatorProfile, ProfileConfig]:
    return PROFILES
