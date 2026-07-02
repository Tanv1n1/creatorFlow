from creatorflow.db.models.user import CreatorProfile
from creatorflow.services.profiles import all_profiles, get as get_profile


def welcome() -> str:
    return (
        "🎬 *Welcome to CreatorFlow!*\n\n"
        "I edit your raw videos automatically — remove pauses, add subtitles, "
        "suggest captions and thumbnails. All in a few minutes.\n\n"
        "*What would you like to do?*"
    )


def profile_select() -> str:
    lines = [f"{cfg.emoji} *{cfg.name}* — {cfg.description}" for _, cfg in all_profiles().items()]
    return "What kind of content do you make?\nThis helps me edit your videos the right way.\n\n" + "\n".join(lines)


def profile_confirmed(profile: CreatorProfile) -> str:
    cfg = get_profile(profile)
    return (
        f"{cfg.emoji} *Profile set: {cfg.name}*\n\n"
        f"I'll optimise every video for *{cfg.description}*.\n\n"
        "*Now send your video:*\n"
        "• Under 50 MB → just send it as a video or file\n"
        "• Over 50 MB → type /bigupload"
    )


def upload_guide(large: bool = False) -> str:
    if large:
        return (
            "📤 *Large video upload*\n\n"
            "Your video is too large to send here directly.\n\n"
            "I'll send you a secure upload link. Click it, pick your file, and you're done.\n\n"
            "Come back here after uploading and type /confirm"
        )
    return (
        "📹 *Send your video*\n\n"
        "Just send your video file as a message and I'll take it from there.\n\n"
        "*Requirements:*\n"
        "• 30 seconds to 3 minutes long\n"
        "• Portrait orientation (how your phone records)\n"
        "• Clear audio (no loud background noise)\n"
        "• Under 50 MB — over that? Type /bigupload"
    )


def how_it_works() -> str:
    return (
        "❓ *How CreatorFlow works*\n\n"
        "*What I do*\n"
        "You send a raw recording. I automatically:\n"
        "✓ Remove pauses and filler words (um, like, basically)\n"
        "✓ Smooth out moments where you restarted a sentence\n"
        "✓ Add English subtitles\n"
        "✓ Suggest captions and thumbnails\n"
        "✓ Give you a quality score with tips\n\n"
        "⏱️ *How long does it take?*\n2–5 minutes for most videos.\n\n"
        "🎙️ *What are filler words?*\n'Um', 'like', 'basically' — words we say while thinking. I remove them so you sound polished.\n\n"
        "🔄 *What are restarts?*\nWhen you stopped and re-recorded a sentence. I detect and smooth them out.\n\n"
        "📊 *Quality score?*\n1–4: Needs work • 5–6: OK • 7–8: Good • 9–10: Excellent\n"
        "Most videos score 6–8 — that's normal!\n\n"
        "Type /start to upload your first video"
    )
