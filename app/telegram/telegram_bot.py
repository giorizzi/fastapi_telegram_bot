import inspect
import logging
from typing import Union, Callable, Any, Dict, Optional

from httpx import Client, AsyncClient
from retry import retry

from .telegram_data_models import WebhookInfoReply, WebhookInfo, WebhookSettings, OutMessage, Update, Message


class CommandBlueprints:
    command_routes: Dict[str, Callable] = {}

    def add_command_route(self, path: str, endpoint: Callable[..., Any]) -> None:
        self.command_routes[path] = HandleWrap(endpoint)

    def command(self, path):
        def decorator(func: Callable[..., Any]):
            self.add_command_route(path=path, endpoint=func)
            return func
        return decorator


class HandleWrap:
    def __init__(self, func: Callable):
        self.func = func
        signature = inspect.signature(func)
        assert 'text' in signature.parameters or len(signature) == 0
        self.req_chat_id = 'chat_id' in signature.parameters
        self.req_message = 'message' in signature.parameters

    def __call__(self, text: str, chat_id: int, message: Message):
        kwargs = {
            'text': text,
            'chat_id': chat_id,
            'message': message,
        }
        if not self.req_chat_id:
            kwargs.pop('chat_id')
        if not self.req_message:
            kwargs.pop('message')
        return self.func(**kwargs)


class TelegramBot:
    command_routes: Dict[str, HandleWrap] = {}

    def __init__(self, bot_id: int, bot_token: str, request_client: Union[Client, AsyncClient, None] = None,
                 logger=logging.getLogger(), blueprints: Optional[CommandBlueprints] = None):
        self.bot_id = bot_id
        self.bot_token = bot_token
        self.api_url = 'https://api.telegram.org/bot' + str(self.bot_id) + ':' + self.bot_token
        if request_client is None:
            request_client = Client()
        self.request_client = request_client
        self.logger = logger
        if blueprints is not None:
            self.register_routes(blueprints=blueprints)

    def get_webhook_info(self) -> WebhookInfo:
        with Client() as client:
            r = client.get(self.api_url + '/getWebhookInfo')
        reply = WebhookInfoReply.parse_raw(r.text)
        assert reply.ok, AssertionError(r.json())
        return reply.result

    @retry(tries=2, delay=2)
    def set_webhook(self, url: str) -> None:
        webhook_info = self.get_webhook_info()
        if webhook_info.url == url:
            return
        payload = WebhookSettings(url=url)
        with Client() as client:
            r = client.get(self.api_url + '/setWebhook', params=payload.dict())
        assert r.json().pop('result', None), AssertionError(r.json())

    async def send_message(self, message: OutMessage):
        response = await self.request_client.post(url=self.api_url + '/sendMessage', data=message.dict())
        return response

    def send_message_sync(self, message: OutMessage):
        assert isinstance(self.request_client, Client)
        response = self.request_client.post(url=self.api_url + '/sendMessage', data=message.dict())
        return response

    async def handle_update(self, update: Update):
        message = update.message
        if update.message is None:
            message = update.edited_message
        assert message is not None
        text = message.text
        chat_id = message.chat.id
        self.logger.info(f'{self.bot_id} is handling this update {update}')
        if text and text.startswith('/'):
            splits = text.split(' ', maxsplit=1)
            command = splits[0]
            if command not in self.command_routes:
                out_text = 'did not undertstand'
            else:
                if len(splits) == 1:
                    command_input = None
                else:
                    command_input = splits[1]
                out_text = await self.command_routes[command](command_input, chat_id, message)
            out_message = OutMessage(chat_id=chat_id, text=out_text)
            self.logger.info(f'{self.bot_id} is replying {out_message}')
            return await self.send_message(out_message)

    def add_command_route(self, path: str, endpoint: Callable[..., Any]) -> None:
        assert path[0] == '/', ValueError('Command routes should start with /')
        assert path not in self.command_routes, ValueError(f'Command {path} already defined {self.command_routes[path]}')
        self.command_routes[path] = HandleWrap(endpoint)

    def command(self, path):
        def decorator(func: Callable[..., Any]):
            self.add_command_route(path=path, endpoint=func)
            return func
        return decorator

    def register_routes(self, blueprints: CommandBlueprints):
        for path, func in blueprints.command_routes.items():
            self.add_command_route(path=path, endpoint=func)
