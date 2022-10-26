from typing import Optional

from sqlmodel import Field, SQLModel, Relationship, Column, DateTime
import datetime


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = None


class Chat(SQLModel, table=True):
    id: int = Field(primary_key=True)
    first_name: str


class SearchInput(SQLModel, table=False):
    location: str
    start_date: datetime.date
    end_date: datetime.date


class SearchTask(SearchInput, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: Optional[int] = Field(index=True, default=None, foreign_key="chat.id")
    chat: Optional[Chat] = Relationship()
    active: bool = True
    active_id: Optional[int] = None
    created_at_utc: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False)
    last_checked_at_utc: Optional[datetime.datetime] = None
    next_run_at_utc: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.utcnow, nullable=False)
    queued: bool = False
