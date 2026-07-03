import random
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.main import db
from database.methods.pull_request import get_reviews_by_user
from database.methods.user import get_user, update_user_activity
from database.models.pull_request import PullRequest
from database.models.user import User
from misc.exceptions import AppError
from misc.schemas.users import (
    GetReviewResponse,
    MassDeactivateRequest,
    MassDeactivateResponse,
    SetIsActiveRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])
DbSession = Annotated[AsyncSession, Depends(db.get_session)]


@router.post("/setIsActive", response_model=UserResponse)
async def set_is_active(payload: SetIsActiveRequest, session: DbSession):
    user = await update_user_activity(session, payload.user_id, payload.is_active)
    if not user:
        raise AppError(status_code=404, code="NOT_FOUND", message="User not found")

    await session.commit()
    return {
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "team_name": user.team_name,
            "is_active": user.is_active,
        }
    }


@router.get("/getReview", response_model=GetReviewResponse)
async def get_reviews(user_id: str, session: DbSession):
    user = await get_user(session, user_id)
    if not user:
        raise AppError(status_code=404, code="NOT_FOUND", message="User not found")

    prs = await get_reviews_by_user(session, user_id)
    pr_list = [
        {
            "pull_request_id": pr.pull_request_id,
            "pull_request_name": pr.pull_request_name,
            "author_id": pr.author_id,
            "status": pr.status,
        }
        for pr in prs
    ]
    return {"user_id": user_id, "pull_requests": pr_list}


@router.post("/massDeactivate", response_model=MassDeactivateResponse)
async def mass_deactivate(payload: MassDeactivateRequest, session: DbSession):
    if not payload.user_ids:
        return {"status": "ok", "reassigned_prs": 0}

    # 1. Fetch users to get their team names
    stmt = select(User).where(User.user_id.in_(payload.user_ids))
    users_result = await session.execute(stmt)
    users_to_deactivate = users_result.scalars().all()

    if not users_to_deactivate:
        return {"status": "ok", "reassigned_prs": 0}

    team_names = list({u.team_name for u in users_to_deactivate})

    # 2. Deactivate them
    update_stmt = update(User).where(User.user_id.in_(payload.user_ids)).values(is_active=False)
    await session.execute(update_stmt)

    # 3. Find OPEN PRs from these teams
    pr_stmt = (
        select(PullRequest, User.team_name)
        .join(User, PullRequest.author_id == User.user_id)
        .where(
            PullRequest.status == "OPEN",
            User.team_name.in_(team_names),
        )
    )
    prs_result = await session.execute(pr_stmt)
    prs_with_teams = prs_result.all()

    # 4. Fetch all active users for these teams
    active_stmt = select(User).where(User.team_name.in_(team_names), User.is_active.is_(True))
    active_result = await session.execute(active_stmt)
    active_users = active_result.scalars().all()

    team_active = {team: [] for team in team_names}
    for au in active_users:
        team_active[au.team_name].append(au.user_id)

    reassigned_count = 0
    payload_set = set(payload.user_ids)

    # 5. Process PRs
    for pr, team_name in prs_with_teams:
        current_reviewers = set(pr.assigned_reviewers)
        deactivated_in_pr = current_reviewers.intersection(payload_set)

        if not deactivated_in_pr:
            continue

        new_reviewers = list(current_reviewers - deactivated_in_pr)
        candidates = [
            u for u in team_active[team_name] if u != pr.author_id and u not in new_reviewers
        ]

        for _ in deactivated_in_pr:
            if candidates:
                chosen = random.choice(candidates)
                candidates.remove(chosen)
                new_reviewers.append(chosen)

        pr.assigned_reviewers = new_reviewers
        reassigned_count += 1

    await session.commit()
    return {"status": "ok", "reassigned_prs": reassigned_count}
