from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class PRStatus(StrEnum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: list[str]
    createdAt: datetime | None = None
    mergedAt: datetime | None = None


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus


class CreatePRRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class MergePRRequest(BaseModel):
    pull_request_id: str


class ReassignPRRequest(BaseModel):
    pull_request_id: str
    old_user_id: str


class PRResponse(BaseModel):
    pr: PullRequest


class ReassignPRResponse(BaseModel):
    pr: PullRequest
    replaced_by: str
