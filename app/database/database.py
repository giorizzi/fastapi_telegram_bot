from sqlmodel import create_engine, Session, SQLModel
from contextlib import contextmanager


class Database:  # does this needs to be a singleton?
    def __init__(self, sqlite_file_name: str = "app/database.db", echo=True):
        self.sqlite_file_name = sqlite_file_name
        self.sqlite_url = f"sqlite:///{sqlite_file_name}"
        self.echo = echo
        self.engine_ = None


    @contextmanager
    def get_session(self) -> Session:
        with Session(self.engine) as session:
            yield session

    @property
    def engine(self):
        if not self.engine_:
            self.engine_ = create_engine(self.sqlite_url, echo=self.echo)
        return self.engine_

    def create_all(self):
        from .models import Chat, SearchTask
        SQLModel.metadata.create_all(self.engine)

    def drop_all(self):
        from .models import Chat, SearchTask
        SQLModel.metadata.drop_all(self.engine)

    def __getstate__(self):
        out_dict = self.__dict__
        out_dict['engine'] = None
        return out_dict

