from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.pull_request import PullRequest
from database.models.user import User

async def get_team_stats(session: AsyncSession, team_name: str) -> dict:
    user_count_query = select(func.count()).where(User.team_name == team_name)
    total_users = await session.scalar(user_count_query) or 0
    
    active_query = select(func.count()).where(User.team_name == team_name, User.is_active.is_(True))
    active_users = await session.scalar(active_query) or 0
    
    prs_query = (
        select(PullRequest.status, func.count())
        .select_from(PullRequest)
        .join(User, PullRequest.author_id == User.user_id)
        .where(User.team_name == team_name)
        .group_by(PullRequest.status)
    )
    
    result = await session.execute(prs_query)
    pr_counts = dict(result.all())
    
    open_prs = pr_counts.get("OPEN", 0)
    merged_prs = pr_counts.get("MERGED", 0)
    total_prs = open_prs + merged_prs
    
    return {
        "team_name": team_name,
        "total_users": total_users,
        "active_users": active_users,
        "total_prs": total_prs,
        "open_prs": open_prs,
        "merged_prs": merged_prs,
    }
