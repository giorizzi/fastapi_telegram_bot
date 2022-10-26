from sqlmodel import select

from ..database import Database
from .telegram_bot import CommandBlueprints
from .telegram_data_models import Message
from ..database.models import Chat, SearchInput, SearchTask
from ..database.utils import get_task_tabulate, get_task_summary
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
            task_str = get_task_summary(task)
            session.add(task)
            session.commit()
        return f'you sent the current job:\n {task_str}'

    @blueprints.command('/status')
    async def add_handle(text: str, chat_id: int):
        with db.get_session() as session:
            chat = session.get(Chat, chat_id)
            if not chat:
                return 'you should first /start'
            statement = select(SearchTask).where(SearchTask.chat_id == chat.id, SearchTask.active)
            results = session.exec(statement)
            no_results = True
            for i, task in enumerate(results): # refresh indexes
                no_results = False
                task.active_id = i
                session.add(task)
            session.commit()

            if no_results:
                return 'You do not have any active task'

            results = session.exec(statement)
            table_text = get_task_tabulate(results)
        return table_text

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
            task_str = get_task_summary(task)
            task.active = False
            task.active_id = None
            session.add(task)
            session.commit()
            session.refresh(task)
        return f'you successfully deleted:\n {task_str}'

    @blueprints.command('/help')
    async def help_handle(text: str):
        help_message = '''
        Usage:
        - /start  
              to register your chat
        - /add [locaton:str] [start_date:(yyyy/)mm/dd] [add_date:(yyyy/)mm/dd]  
              schedules a job querying recreation.gov for campsite within 15 miles from location within selected dates
        - /status 
              returns a list of all your active scraping jobs
        - /del [id:int]
              delete a job using the id from /status
        '''
        return help_message

    return blueprints
