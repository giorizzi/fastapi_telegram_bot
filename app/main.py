import logging
import os

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.logger import logger
from starlette.responses import PlainTextResponse

from .database.utils import clear_queued
from .telegram.telegram_bot import TelegramBot
from .telegram.telegram_data_models import Update
from .ngrok_info import get_public_url
from .telegram.commands import blueprint_factory
from .database import Database

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
if __name__ != "main":
    logger.setLevel(gunicorn_logger.level)
else:
    logger.setLevel(logging.DEBUG)

TELEGRAM_BOT_ID = int(os.getenv('TELEGRAM_BOT_ID'))
TELEGRAM_BOT_TOKEN_ = os.getenv('TELEGRAM_BOT_TOKEN')
assert TELEGRAM_BOT_ID is not None
assert TELEGRAM_BOT_TOKEN_ is not None

app = FastAPI()
client = httpx.AsyncClient()
db = Database()
bot = TelegramBot(bot_id=TELEGRAM_BOT_ID, bot_token=TELEGRAM_BOT_TOKEN_, request_client=client, logger=logger,
                  blueprints=blueprint_factory(db=db))


@app.on_event("startup")
async def startup_event():
    ngrok_url = await get_public_url(client=client)
    bot_webhook_url = ngrok_url + f'/hook/{TELEGRAM_BOT_ID}'
    bot.set_webhook(url=bot_webhook_url)
    logger.info(f'Set telegram webhook for bot {TELEGRAM_BOT_ID} at {ngrok_url}')
    clear_queued(db=db)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: Exception):
    logger.info(str(exc))
    return PlainTextResponse(str(exc), status_code=422)


@app.get("/")
async def root():
    logger.info('logger Hello World')
    return {"message": "Hello World"}


@app.post("/hook/{bot_id}")
async def root(bot_id: int, update: Update):
    # Todo: here code to handle multiple bots
    await bot.handle_update(update)
