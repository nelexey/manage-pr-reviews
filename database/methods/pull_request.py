from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.pull_request import PRStatus, PullRequest


async def check_pr_exists(session: AsyncSession, pr_id: str) -> bool:
    stmt = select(PullRequest.pull_request_id).where(PullRequest.pull_request_id == pr_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def create_pr(
    session: AsyncSession, pr_id: str, pr_name: str, author_id: str, reviewers: list[str]
) -> PullRequest:
    pr = PullRequest(
        pull_request_id=pr_id,
        pull_request_name=pr_name,
        author_id=author_id,
        status=PRStatus.OPEN.value,
        assigned_reviewers=reviewers,
    )
    session.add(pr)
    await session.flush()
    return pr


async def get_pr(session: AsyncSession, pr_id: str) -> PullRequest | None:
    stmt = select(PullRequest).where(PullRequest.pull_request_id == pr_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def merge_pr(session: AsyncSession, pr_id: str) -> PullRequest | None:
    pr = await get_pr(session, pr_id)
    if pr and pr.status != PRStatus.MERGED.value:
        pr.status = PRStatus.MERGED.value
        pr.merged_at = datetime.now(UTC).replace(tzinfo=None)
        await session.flush()
    return pr


async def update_pr_reviewers(
    session: AsyncSession, pr_id: str, reviewers: list[str]
) -> PullRequest | None:
    pr = await get_pr(session, pr_id)
    if pr:
        pr.assigned_reviewers = reviewers
        await session.flush()
    return pr


async def get_reviews_by_user(session: AsyncSession, user_id: str) -> list[PullRequest]:
    stmt = select(PullRequest).where(PullRequest.assigned_reviewers.any(user_id))
    result = await session.execute(stmt)
    return list(result.scalars().all())
