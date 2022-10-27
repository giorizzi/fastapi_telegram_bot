from typing import Optional

from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
from datetime import date, datetime


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


class Chat(SQLModel, table=True):
    id: int = Field(primary_key=True)
    first_name: str


class SearchQuery(SQLModel, table=False):
    location: str
    start_date: date
    end_date: date


class SearchTask(SearchQuery, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: Optional[int] = Field(index=True, default=None, foreign_key="chat.id")
    chat: Optional[Chat] = Relationship()
    active: bool = True
    active_id: Optional[int] = None
    created_at_utc: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_checked_at_utc: Optional[datetime] = None
    next_run_at_utc: Optional[datetime] = Field(default_factory=datetime.utcnow, nullable=False)
    queued: bool = False
