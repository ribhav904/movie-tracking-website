from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def set_current_user(session: AsyncSession, user_id: UUID, role: str | None = None) -> None:
    await session.execute(
        text("select set_config('app.current_user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )
    if role is not None:
        await session.execute(
            text("select set_config('app.current_user_role', :role, true)"),
            {"role": role},
        )


async def session_scope(
    factory: async_sessionmaker[AsyncSession],
    user_id: UUID | None = None,
    role: str | None = None,
) -> AsyncIterator[AsyncSession]:
    async with factory() as session, session.begin():
        if user_id is not None:
            await set_current_user(session, user_id, role)
        yield session
