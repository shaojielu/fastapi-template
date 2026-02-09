import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session
from app.schemas.users import UserCreate
from app.services.user import create_user, get_user_by_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    user = await get_user_by_email(session, settings.FIRST_SUPERUSER)
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        await create_user(session, user_in)
        await session.commit()


async def main() -> None:
    logger.info("Creating initial data")
    async with async_session() as session:
        await init_db(session)
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
