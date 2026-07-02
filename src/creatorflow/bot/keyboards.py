from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from creatorflow.services.profiles import all_profiles
from creatorflow.db.models.user import CreatorProfile

PROFILE_PREFIX = "profile:"
WELCOME_PREFIX = "welcome:"
SETTINGS_PREFIX = "setprofile:"


def welcome_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📹 Upload & edit a video", callback_data=f"{WELCOME_PREFIX}upload")],
        [InlineKeyboardButton("📂 Check my past videos", callback_data=f"{WELCOME_PREFIX}history")],
        [InlineKeyboardButton("⚙️ Settings", callback_data=f"{WELCOME_PREFIX}settings")],
        [InlineKeyboardButton("❓ How does this work?", callback_data=f"{WELCOME_PREFIX}howto")],
    ]
    return InlineKeyboardMarkup(rows)


def profile_select(prefix: str = PROFILE_PREFIX) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{cfg.emoji} {cfg.name}", callback_data=f"{prefix}{p.value}")]
        for p, cfg in all_profiles().items()
    ]
    return InlineKeyboardMarkup(rows)


def parse_profile(callback_data: str, prefix: str) -> CreatorProfile | None:
    if not callback_data.startswith(prefix):
        return None
    raw = callback_data[len(prefix):]
    try:
        return CreatorProfile(raw)
    except ValueError:
        return None
