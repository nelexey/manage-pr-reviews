from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.main import db
from database.methods.team import check_team_exists, create_team, get_team_with_members
from database.methods.user import upsert_users
from misc.exceptions import AppError
from misc.schemas.teams import Team, TeamResponse

router = APIRouter(prefix="/team", tags=["Teams"])
DbSession = Annotated[AsyncSession, Depends(db.get_session)]


@router.post("/add", status_code=201, response_model=TeamResponse)
async def create_team_handler(payload: Team, session: DbSession):
    if await check_team_exists(session, payload.team_name):
        raise AppError(status_code=400, code="TEAM_EXISTS", message="team_name already exists")

    await create_team(session, payload.team_name)
    await upsert_users(session, payload.team_name, payload.members)
    await session.commit()

    return {"team": payload.model_dump()}


@router.get("/get", response_model=Team)
async def get_team(team_name: str, session: DbSession):
    team, users = await get_team_with_members(session, team_name)
    if not team:
        raise AppError(status_code=404, code="NOT_FOUND", message="Team not found")

    members = [
        {"user_id": u.user_id, "username": u.username, "is_active": u.is_active} for u in users
    ]
    return {"team_name": team.team_name, "members": members}
