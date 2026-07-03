from pydantic import BaseModel


class TeamStatsResponse(BaseModel):
    team_name: str
    total_users: int
    active_users: int
    total_prs: int
    open_prs: int
    merged_prs: int
