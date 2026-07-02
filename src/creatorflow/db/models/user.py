import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from creatorflow.db.engine import Base


class CreatorProfile(str, enum.Enum):
    CREATOR   = "creator"    # Instagram / TikTok / Shorts
    COACH     = "coach"      # Courses, tutorials
    PODCASTER = "podcaster"  # Audio-focused
    BUSINESS  = "business"   # Demos, testimonials


class UserProfile(Base):
    __tablename__ = "user_profiles"

    discord_user_id: Mapped[str]      = mapped_column(String(32), primary_key=True)
    profile:         Mapped[CreatorProfile] = mapped_column(SAEnum(CreatorProfile), default=CreatorProfile.CREATOR)
    display_name:    Mapped[str|None] = mapped_column(String(128), nullable=True)

    prefer_captions:     Mapped[bool] = mapped_column(Boolean, default=True)
    prefer_subtitles:    Mapped[bool] = mapped_column(Boolean, default=True)
    prefer_thumbnails:   Mapped[bool] = mapped_column(Boolean, default=True)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
