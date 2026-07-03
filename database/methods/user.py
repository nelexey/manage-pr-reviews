from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from misc.schemas.teams import TeamMember


async def upsert_users(session: AsyncSession, team_name: str, members: list[TeamMember]) -> None:
    if not members:
        return

    values = [
        {
            "user_id": m.user_id,
            "username": m.username,
            "team_name": team_name,
            "is_active": m.is_active,
        }
        for m in members
    ]

    stmt = pg_insert(User).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={
            "username": stmt.excluded.username,
            "team_name": stmt.excluded.team_name,
            "is_active": stmt.excluded.is_active,
        },
    )
    await session.execute(stmt)
    await session.flush()


async def update_user_activity(session: AsyncSession, user_id: str, is_active: bool) -> User | None:
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.is_active = is_active
        await session.flush()
    return user


async def get_user(session: AsyncSession, user_id: str) -> User | None:
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_candidate_reviewers(
    session: AsyncSession, team_name: str, exclude_user_ids: list[str]
) -> list[User]:
    stmt = select(User).where(
        User.team_name == team_name, User.is_active.is_(True), User.user_id.notin_(exclude_user_ids)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
