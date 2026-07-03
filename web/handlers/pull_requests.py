import random
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.main import db
from database.methods.pull_request import (
    check_pr_exists,
    create_pr,
    get_pr,
    merge_pr,
    update_pr_reviewers,
)
from database.methods.user import get_candidate_reviewers, get_user
from misc.exceptions import AppError
from misc.schemas.pull_requests import (
    CreatePRRequest,
    MergePRRequest,
    PRResponse,
    ReassignPRRequest,
    ReassignPRResponse,
)

router = APIRouter(prefix="/pullRequest", tags=["PullRequests"])
DbSession = Annotated[AsyncSession, Depends(db.get_session)]


@router.post("/create", status_code=201, response_model=PRResponse)
async def create_pull_request(payload: CreatePRRequest, session: DbSession):
    if await check_pr_exists(session, payload.pull_request_id):
        raise AppError(status_code=409, code="PR_EXISTS", message="PR already exists")

    author = await get_user(session, payload.author_id)
    if not author:
        raise AppError(status_code=404, code="NOT_FOUND", message="Author not found")

    candidates = await get_candidate_reviewers(
        session, author.team_name, exclude_user_ids=[author.user_id]
    )
    reviewers = random.sample(candidates, min(2, len(candidates)))
    reviewer_ids = [r.user_id for r in reviewers]

    pr = await create_pr(
        session, payload.pull_request_id, payload.pull_request_name, payload.author_id, reviewer_ids
    )
    await session.commit()

    return {
        "pr": {
            "pull_request_id": pr.pull_request_id,
            "pull_request_name": pr.pull_request_name,
            "author_id": pr.author_id,
            "status": pr.status,
            "assigned_reviewers": pr.assigned_reviewers,
            "createdAt": pr.created_at,
            "mergedAt": pr.merged_at,
        }
    }


@router.post("/merge", response_model=PRResponse)
async def merge_pull_request(payload: MergePRRequest, session: DbSession):
    pr = await merge_pr(session, payload.pull_request_id)
    if not pr:
        raise AppError(status_code=404, code="NOT_FOUND", message="PR not found")

    await session.commit()
    return {
        "pr": {
            "pull_request_id": pr.pull_request_id,
            "pull_request_name": pr.pull_request_name,
            "author_id": pr.author_id,
            "status": pr.status,
            "assigned_reviewers": pr.assigned_reviewers,
            "createdAt": pr.created_at,
            "mergedAt": pr.merged_at,
        }
    }


@router.post("/reassign", response_model=ReassignPRResponse)
async def reassign_reviewer(payload: ReassignPRRequest, session: DbSession):
    pr = await get_pr(session, payload.pull_request_id)
    if not pr:
        raise AppError(status_code=404, code="NOT_FOUND", message="PR not found")

    if pr.status == "MERGED":
        raise AppError(status_code=409, code="PR_MERGED", message="cannot reassign on merged PR")

    if payload.old_user_id not in pr.assigned_reviewers:
        raise AppError(
            status_code=409, code="NOT_ASSIGNED", message="reviewer is not assigned to this PR"
        )

    old_user = await get_user(session, payload.old_user_id)
    if not old_user:
        raise AppError(status_code=404, code="NOT_FOUND", message="Old user not found")

    exclude_ids = [pr.author_id] + pr.assigned_reviewers
    candidates = await get_candidate_reviewers(session, old_user.team_name, exclude_ids)

    if not candidates:
        raise AppError(
            status_code=409, code="NO_CANDIDATE", message="no active replacement candidate in team"
        )

    new_reviewer = random.choice(candidates)

    new_reviewers = [
        new_reviewer.user_id if r == payload.old_user_id else r for r in pr.assigned_reviewers
    ]
    await update_pr_reviewers(session, pr.pull_request_id, new_reviewers)
    await session.commit()

    return {
        "pr": {
            "pull_request_id": pr.pull_request_id,
            "pull_request_name": pr.pull_request_name,
            "author_id": pr.author_id,
            "status": pr.status,
            "assigned_reviewers": pr.assigned_reviewers,
            "createdAt": pr.created_at,
            "mergedAt": pr.merged_at,
        },
        "replaced_by": new_reviewer.user_id,
    }
