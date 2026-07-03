from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Team(Base):
    __tablename__ = "teams"

    team_name: Mapped[str] = mapped_column(String, primary_key=True)
