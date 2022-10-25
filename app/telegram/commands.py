from ..database import get_session
from .telegram_bot import CommandBlueprints
from .telegram_data_models import Message
from ..database.models import Chat

blueprints = CommandBlueprints()


@blueprints.command('/echo')
async def echo_text(text):
    return text


@blueprints.command('/start')
async def start_handle(text: str, chat_id: int, message: Message):
    with get_session() as session:
        chat = session.get(Chat, chat_id)
        if chat is None:
            chat = Chat(id=chat_id, first_name=message.chat.first_name)
            session.add(chat)
            session.commit()
            return f'Hi {chat.first_name}, welcome'
        return f'Hi {chat.first_name}, welcome back'
