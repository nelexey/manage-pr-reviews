from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from misc.exceptions import AppError

from database.main import db
from database.methods.user import update_user_activity, get_user
from database.methods.pull_request import get_reviews_by_user
from misc.schemas.users import SetIsActiveRequest, UserResponse, GetReviewResponse

router = APIRouter(prefix="/users", tags=["Users"])
DbSession = Annotated[AsyncSession, Depends(db.get_session)]

@router.post("/setIsActive", response_model=UserResponse)
async def set_is_active(payload: SetIsActiveRequest, session: DbSession):
    user = await update_user_activity(session, payload.user_id, payload.is_active)
    if not user:
        raise AppError(status_code=404, code="NOT_FOUND", message="User not found")
    
    await session.commit()
    return {"user": {"user_id": user.user_id, "username": user.username, "team_name": user.team_name, "is_active": user.is_active}}

@router.get("/getReview", response_model=GetReviewResponse)
async def get_reviews(user_id: str, session: DbSession):
    user = await get_user(session, user_id)
    if not user:
        raise AppError(status_code=404, code="NOT_FOUND", message="User not found")
    
    prs = await get_reviews_by_user(session, user_id)
    pr_list = [{"pull_request_id": pr.pull_request_id, "pull_request_name": pr.pull_request_name, "author_id": pr.author_id, "status": pr.status} for pr in prs]
    return {"user_id": user_id, "pull_requests": pr_list}