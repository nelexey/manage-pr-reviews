from pydantic import BaseModel

from .pull_requests import PullRequestShort


class User(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool


class SetIsActiveRequest(BaseModel):
    user_id: str
    is_active: bool


class UserResponse(BaseModel):
    user: User


class GetReviewResponse(BaseModel):
    user_id: str
    pull_requests: list[PullRequestShort]


class MassDeactivateRequest(BaseModel):
    user_ids: list[str]


class MassDeactivateResponse(BaseModel):
    status: str
    reassigned_prs: int
