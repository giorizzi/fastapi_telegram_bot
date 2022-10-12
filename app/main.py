import logging

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.logger import logger
from starlette.responses import PlainTextResponse
from telegram_bot import set_webhook, TELEGRAM_BOT_ID, send_message
from ngrok_info import get_public_url
from telegram_data_models import Update, OutMessage

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
if __name__ != "main":
    logger.setLevel(gunicorn_logger.level)
else:
    logger.setLevel(logging.DEBUG)

app = FastAPI()
client = httpx.AsyncClient()


@app.on_event("startup")
async def startup_event():
    ngrok_url = await get_public_url(client=client)
    bot_webhook_url = ngrok_url + f'/hook/{TELEGRAM_BOT_ID}'
    set_webhook(url=bot_webhook_url)
    logger.info(f'Set telegram webhook for bot {TELEGRAM_BOT_ID} at {ngrok_url}')


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: Exception):
    logger.info(str(exc))
    return PlainTextResponse(str(exc), status_code=422)


@app.get("/")
async def root():
    logger.info('logger Hello World')
    return {"message": "Hello World"}


@app.post("/hook/{bot_id}")
async def root(bot_id: int, data: Update):
    chat_id = data.message.from_.id
    logger.info(f'received from {bot_id} this update {data}')
    text = data.message.text
    out_message = OutMessage(chat_id=chat_id, text=text)
    response = await send_message(message=out_message, client=client)
    logger.info(f'receiver {response} after sending {out_message}')
