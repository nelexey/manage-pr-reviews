from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.main import db
from database.methods.stats import get_team_stats
from database.methods.team import check_team_exists
from misc.exceptions import AppError
from misc.schemas.stats import TeamStatsResponse

router = APIRouter(prefix="/stats", tags=["Statistics"])
DbSession = Annotated[AsyncSession, Depends(db.get_session)]

@router.get("/team/{team_name}", response_model=TeamStatsResponse)
async def get_team_statistics(team_name: str, session: DbSession):
    if not await check_team_exists(session, team_name):
        raise AppError(status_code=404, code="NOT_FOUND", message="Team not found")
        
    stats = await get_team_stats(session, team_name)
    return stats
