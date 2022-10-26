from sqlmodel import select

from ..database import Database
from .telegram_bot import CommandBlueprints
from .telegram_data_models import Message
from ..database.models import Chat, SearchInput, SearchTask
from ..worker import delayed_reply
from .text_parser import TextInputParser



def blueprint_factory(db=Database()):
    blueprints = CommandBlueprints()

    @blueprints.command('/echo')
    async def echo_text(text):
        if text is None:
            text = ''
        return text

    @blueprints.command('/start')
    async def start_handle(text: str, chat_id: int, message: Message):
        with db.get_session() as session:
            chat = session.get(Chat, chat_id)
            if chat is None:
                chat = Chat(id=chat_id, first_name=message.chat.first_name)
                session.add(chat)
                session.commit()
                return f'Hi {chat.first_name}, welcome'
            return f'Hi {chat.first_name}, welcome back'

    @blueprints.command('/delay')
    async def delay_handle(text: str, chat_id: int):
        seconds = int(text)
        task = delayed_reply.delay(chat_id, seconds)
        return f'Hi you should get a message in {seconds}s'

    @blueprints.command('/add')
    async def add_handle(text: str, chat_id: int):
        parser = TextInputParser(SearchInput)
        try:
            search_request = parser.parse(text)
        except ValueError as e:
            return f'input is not correct, {e}'
        with db.get_session() as session:
            chat = session.get(Chat, chat_id)
            task = SearchTask(chat=chat, **search_request.dict())
            session.add(task)
            session.commit()
        return f'you sent the current {search_request}'

    @blueprints.command('/status')
    async def add_handle(text: str, chat_id: int):
        with db.get_session() as session:
            chat = session.get(Chat, chat_id)
            if not chat:
                return 'you should first /start'
            statement = select(SearchTask).where(SearchTask.chat_id == chat.id, SearchTask.active)
            results = session.exec(statement)
            message = ''
            for i, task in enumerate(results):
                task.active_id = i
                message += f'{task.active_id} {task.location} {task.start_date} {task.end_date} {task.last_checked_at_utc}\n'
                session.add(task)
            session.commit()
            if not message:
                message = 'you do not have any active task'
        return message

    @blueprints.command('/del')
    async def add_handle(text: str, chat_id: int):
        try:
            task_active_id = int(text)
        except:
            return '/del id[int]  is the proper usage'
        with db.get_session() as session:
            chat = session.get(Chat, chat_id)
            if not chat:
                return 'you should first /start'
            statement = select(SearchTask).where(SearchTask.chat_id == chat.id, SearchTask.active_id == task_active_id, SearchTask.active)
            task = session.exec(statement).first()
            task.active = False
            task.active_id = None
            session.add(task)
            session.commit()
            session.refresh(task)
        return f'you successfully deleted {task}'

    return blueprints
