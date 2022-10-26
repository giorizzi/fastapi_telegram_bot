import os
from typing import Optional

import httpx
from pydantic import BaseModel
from retry import retry

from telegram_data_models import WebhookInfoReply, WebhookInfo, WebhookSettings, OutMessage

TELEGRAM_BOT_ID = os.getenv('TELEGRAM_BOT_ID')
TELEGRAM_BOT_TOKEN_ = os.getenv('TELEGRAM_BOT_TOKEN')
bot_api_url = 'https://api.telegram.org/bot' + TELEGRAM_BOT_ID + ':' + TELEGRAM_BOT_TOKEN_


def get_webhook_info() -> WebhookInfo:
    r = httpx.get(bot_api_url + '/getWebhookInfo')
    reply = WebhookInfoReply.parse_raw(r.text)
    assert reply.ok, AssertionError(r.json())
    return reply.result


@retry(tries=2, delay=2)
def set_webhook(url: str):
    webhook_info = get_webhook_info()
    if webhook_info.url == url:
        return True
    payload = WebhookSettings(url=url)
    r = httpx.get(bot_api_url + '/setWebhook', params=payload.dict())
    assert r.json().pop('result', None), AssertionError(r.json())


async def send_message(message: OutMessage, client):
    response = await client.post(url=bot_api_url + '/sendMessage', data=message.dict())
    return response
