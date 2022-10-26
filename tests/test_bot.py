from contextlib import contextmanager

import httpx
import pytest
from sqlmodel import create_engine, Session

from app.telegram.telegram_bot import TelegramBot
from app.telegram.telegram_data_models import Update, Message, User, Chat
from app.database import Database
from app.database.models import Chat as db_Chat
from app.telegram.commands import blueprint_factory



def build_update(text: str)-> Update:
    user = User(id=12345, is_bot=False, first_name='user', language_code='en')
    chat = Chat(id=12345, first_name='user', type='private')
    message_raw = {
    'message_id': 60,
    'from': user.dict(),
    'chat': chat.dict(),
    'date': 1666000000,
    'text': text,
    'animation': None,
    'document': None,
    }
    message = Message.parse_obj(message_raw)
    update = Update(update_id=74241250, message=message)
    return update


@pytest.fixture
def db():
    sqlite_file_name = "test_database.db"
    db = Database(sqlite_file_name=sqlite_file_name, echo=False)
    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture
def bot(db):
    TELEGRAM_BOT_ID = 1234567
    TELEGRAM_BOT_TOKEN_ = 'abcdefghi'
    bot = TelegramBot(bot_id=TELEGRAM_BOT_ID, bot_token=TELEGRAM_BOT_TOKEN_, request_client=httpx.AsyncClient())
    if not bot.command_routes:
        bot.register_routes(blueprint_factory(db))
    return bot


def test_basic(bot):
    assert bot.bot_id == 1234567, f'{bot}'


@pytest.mark.asyncio
async def test_echo(bot, httpx_mock):
    httpx_mock.add_response(url=bot.api_url + '/sendMessage', json='{True}', match_content=b'chat_id=12345&text=test')
    response = await bot.handle_update(build_update('/echo test'))

@pytest.mark.asyncio
async def test_start(bot, httpx_mock, db):
    update = build_update('/start')
    chat_id = update.message.chat.id
    httpx_mock.add_response(url=bot.api_url + '/sendMessage', json='{True}',
                            match_content=b'chat_id=12345&text=Hi+user%2C+welcome')
    response = await bot.handle_update(update)
    with db.get_session() as session:
        chat = session.get(db_Chat, chat_id)
        assert chat and chat.first_name == 'user'

