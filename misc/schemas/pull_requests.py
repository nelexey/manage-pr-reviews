from typing import List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class PRStatus(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"

class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: List[str]
    createdAt: Optional[datetime] = None
    mergedAt: Optional[datetime] = None

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