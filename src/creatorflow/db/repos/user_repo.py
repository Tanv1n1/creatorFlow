from sqlalchemy import select, update

from creatorflow.db.engine import AsyncSessionLocal
from creatorflow.db.models.user import UserProfile, CreatorProfile


async def get_or_create(user_id: str, display_name: str | None = None) -> UserProfile:
    async with AsyncSessionLocal() as s:
        profile = await s.get(UserProfile, user_id)
        if profile is None:
            profile = UserProfile(telegram_user_id=user_id, display_name=display_name)
            s.add(profile)
            await s.commit()
            await s.refresh(profile)
        return profile


async def get(user_id: str) -> UserProfile | None:
    async with AsyncSessionLocal() as s:
        return await s.get(UserProfile, user_id)


async def set_profile(user_id: str, profile: CreatorProfile) -> None:
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(UserProfile).where(UserProfile.telegram_user_id == user_id).values(profile=profile)
        )
        await s.commit()


async def mark_onboarded(user_id: str, display_name: str | None = None) -> None:
    values: dict = {"onboarding_complete": True}
    if display_name:
        values["display_name"] = display_name
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(UserProfile).where(UserProfile.telegram_user_id == user_id).values(**values)
        )
        await s.commit()


async def update_preferences(user_id: str, **kwargs) -> None:
    allowed = {"prefer_captions", "prefer_subtitles", "prefer_thumbnails"}
    values = {k: v for k, v in kwargs.items() if k in allowed}
    if not values:
        return
    async with AsyncSessionLocal() as s:
        await s.execute(
            update(UserProfile).where(UserProfile.telegram_user_id == user_id).values(**values)
        )
        await s.commit()
