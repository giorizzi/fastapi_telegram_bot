from sqlmodel import create_engine, Session, SQLModel
from contextlib import contextmanager

sqlite_file_name = "app/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session


def create_all():
    SQLModel.metadata.create_all(engine)
