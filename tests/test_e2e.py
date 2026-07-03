import os
import random
import string

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

API_BASE_URL = "http://localhost:8080"

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "1234")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pr_db")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def generate_random_string(length=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

@pytest.fixture(scope="module")
def api_client():
    with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
        yield client

@pytest_asyncio.fixture(scope="module")
async def db_session():
    async with async_session() as session:
        yield session
    await engine.dispose()

@pytest_asyncio.fixture(scope="module")
async def test_team(db_session, api_client):
    team_name = f"e2e_team_{generate_random_string()}"
    users = [
        {"user_id": f"u_{team_name}_1", "username": "User 1", "is_active": True},
        {"user_id": f"u_{team_name}_2", "username": "User 2", "is_active": True},
        {"user_id": f"u_{team_name}_3", "username": "User 3", "is_active": True},
        {"user_id": f"u_{team_name}_4", "username": "User 4", "is_active": True},
    ]

    response = api_client.post("/team/add", json={"team_name": team_name, "members": users})
    assert response.status_code == 201

    yield team_name, users

    # Teardown: Clean up using database cascade
    await db_session.execute(text("DELETE FROM teams WHERE team_name = :t"), {"t": team_name})
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_team(api_client, test_team):
    team_name, expected_users = test_team
    response = api_client.get(f"/team/get?team_name={team_name}")
    assert response.status_code == 200
    data = response.json()
    assert data["team_name"] == team_name
    assert len(data["members"]) == 4

@pytest.mark.asyncio
async def test_create_pull_request(api_client, test_team):
    team_name, expected_users = test_team
    author_id = expected_users[0]["user_id"]

    response = api_client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": f"pr_{generate_random_string()}",
            "pull_request_name": "Fix tests",
            "author_id": author_id,
        },
    )
    assert response.status_code == 201
    data = response.json()["pr"]
    assert len(data["assigned_reviewers"]) == 2
    assert author_id not in data["assigned_reviewers"]

@pytest.mark.asyncio
async def test_user_activity(api_client, test_team):
    team_name, expected_users = test_team
    user_to_deactivate = expected_users[3]["user_id"]

    res = api_client.post("/users/setIsActive", json={"user_id": user_to_deactivate, "is_active": False})
    assert res.status_code == 200

    res_team = api_client.get(f"/team/get?team_name={team_name}")
    member = next(m for m in res_team.json()["members"] if m["user_id"] == user_to_deactivate)
    assert member["is_active"] is False

@pytest.mark.asyncio
async def test_mass_deactivate_and_reassign(api_client, test_team):
    team_name, expected_users = test_team
    author_id = expected_users[0]["user_id"]
    
    pr_id = f"pr_{generate_random_string()}"
    res_create = api_client.post(
        "/pullRequest/create",
        json={"pull_request_id": pr_id, "pull_request_name": "Mass", "author_id": author_id},
    )
    assigned_reviewers = res_create.json()["pr"]["assigned_reviewers"]
    target_reviewer = assigned_reviewers[0]
    
    res_mass = api_client.post("/users/massDeactivate", json={"user_ids": [target_reviewer]})
    assert res_mass.status_code == 200
    assert res_mass.json()["reassigned_prs"] >= 1

    survivor_reviewer = assigned_reviewers[1]
    res_review = api_client.get(f"/users/getReview?user_id={survivor_reviewer}")
    assert res_review.status_code == 200
