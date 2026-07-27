from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database.models import UserSettings, User
from datetime import datetime
from typing import Optional

async def get_user_settings(user_id: int) -> Optional[UserSettings]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
        return settings

async def update_setting(user_id: int, setting_name: str, value: bool) -> Optional[UserSettings]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
        if hasattr(settings, setting_name):
            setattr(settings, setting_name, value)
            settings.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(settings)
            return settings
        return None
