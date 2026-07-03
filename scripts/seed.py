import asyncio
import os
import random
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.main import db
from database.models.team import Team
from database.models.user import User


async def seed():
    async with db.session_factory() as session:
        teams = []
        users = []

        for i in range(100):
            team_name = f"team_{i}"
            teams.append(Team(team_name=team_name))

            num_members = random.randint(3, 1000)
            for j in range(num_members):
                user_id = f"u_{team_name}_{j}"
                is_active = random.choice([True, False])
                users.append(
                    User(
                        user_id=user_id,
                        username=f"User {j} of {team_name}",
                        team_name=team_name,
                        is_active=is_active,
                    )
                )

        session.add_all(teams)
        session.add_all(users)

        await session.commit()
        print(f"Создано {len(teams)} команд и {len(users)} пользователей.")


if __name__ == "__main__":
    asyncio.run(seed())
