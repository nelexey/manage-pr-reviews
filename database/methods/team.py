from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.team import Team
from database.models.user import User

async def create_team(session: AsyncSession, team_name: str) -> Team:
    team = Team(team_name=team_name)
    session.add(team)
    await session.flush()
    return team

async def check_team_exists(session: AsyncSession, team_name: str) -> bool:
    stmt = select(Team.team_name).where(Team.team_name == team_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None

async def get_team_with_members(session: AsyncSession, team_name: str) -> tuple[Optional[Team], list[User]]:
    stmt = select(Team).where(Team.team_name == team_name)
    result = await session.execute(stmt)
    team = result.scalar_one_or_none()
    
    if not team:
        return None, []
        
    users_stmt = select(User).where(User.team_name == team_name)
    users_result = await session.execute(users_stmt)
    users = list(users_result.scalars().all())
    
    return team, users
