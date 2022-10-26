import pytest
import datetime

from sqlmodel import select
from app.database.models import Chat, SearchTask, SearchInput
from app.database import Database


@pytest.fixture
def db():
    sqlite_file_name = "test_database.db"
    db = Database(sqlite_file_name=sqlite_file_name, echo=False)
    db.create_all()
    yield db
    db.drop_all()

@pytest.fixture
def task(db):
    start_date = datetime.datetime.now().date() + datetime.timedelta(days=90)
    end_date = start_date + datetime.timedelta(days=5)

    input = SearchInput(location='grand canyon', start_date=start_date,
                        end_date=end_date)
    chat = Chat(id=1234, first_name='user')
    with db.get_session() as session:
        task = SearchTask(chat=chat, **input.dict())
        session.add(chat)
        session.add(task)
        session.commit()
    yield task




def test_add_chat(db):
    with db.get_session() as session:
        chat = Chat(id=123, first_name='user')
        session.add(chat)
        session.commit()
        db_chat = session.get(Chat, 123)
        assert db_chat.first_name == 'user'


def test_task(db):
    start_date = datetime.datetime.now().date() + datetime.timedelta(days=90)
    end_date = start_date + datetime.timedelta(days=5)

    input = SearchInput(location='grand canyon', start_date=start_date,
                        end_date=end_date)
    with db.get_session() as session:
        chat = Chat(id=1234, first_name='user')
        task = SearchTask(chat=chat, **input.dict())
        session.add(chat)
        session.add(task)
        session.commit()
        statement = select(SearchTask).where(SearchTask.chat == chat)
        task = session.exec(statement).first()
        assert task.location == 'grand canyon'

        statement = select(SearchTask).where(SearchTask.chat_id == 1234)
        task = session.exec(statement).first()
        assert task.location == 'grand canyon'


def test_task_retrieve(db):
    start_date = datetime.datetime.now().date() + datetime.timedelta(days=90)
    end_date = start_date + datetime.timedelta(days=5)

    input = SearchInput(location='grand canyon', start_date=start_date,
                        end_date=end_date)
    with db.get_session() as session:
        chat = Chat(id=1234, first_name='user')
        task = SearchTask(chat=chat, **input.dict())
        session.add(chat)
        session.add(task)
        session.commit()
        statement = select(SearchTask).where(SearchTask.active, SearchTask.next_run_at_utc < datetime.datetime.utcnow())
        tasks = session.exec(statement)
        for task in tasks:
            print(task)
        assert tasks

def test_task_update(db, task):
    print(task)
    with db.get_session() as session:
        statement = select(SearchTask).where(SearchTask.active, SearchTask.next_run_at_utc < datetime.datetime.utcnow())
        task = session.exec(statement).first()
        print(task)
    print(task)
    assert task.active



