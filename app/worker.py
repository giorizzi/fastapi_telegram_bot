import datetime
import os
import time
from sqlmodel import select

from .database.utils import get_task_summary
from .scraper import get_availability

import httpx
from celery import Celery

from .telegram.telegram_bot import TelegramBot
from .telegram.telegram_data_models import OutMessage

from .database import Database
from .database.models import SearchTask

TELEGRAM_BOT_ID = int(os.getenv('TELEGRAM_BOT_ID', 123456))
TELEGRAM_BOT_TOKEN_ = os.getenv('TELEGRAM_BOT_TOKEN', 'abcdefg')
assert TELEGRAM_BOT_ID is not None
assert TELEGRAM_BOT_TOKEN_ is not None

client = httpx.Client()
sender_bot = TelegramBot(bot_id=TELEGRAM_BOT_ID, bot_token=TELEGRAM_BOT_TOKEN_, request_client=client)
celery = Celery(__name__)
celery.conf.broker_url = "redis://redis:6379"
celery.conf.result_backend = "redis://redis:6379"
db = Database()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(30.0, scan_for_expired.s(), name='scan_for_expired', expires=50)


@celery.task
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True


@celery.task
def delayed_reply(chat_id, time_out):
    message = OutMessage(chat_id=chat_id, text='message from celery')
    time.sleep(time_out)
    sender_bot.send_message_sync(message=message)
    return True


@celery.task
def run_task(task_id: int):
    with db.get_session() as session:
        task = session.get(SearchTask, task_id)
        chat_id = task.chat.id
    try:
        results = get_close_campsite(task)

        if results:
            text = f'HURRY, I found the following available campsites:\n{get_task_summary(task)}\n {results}'
            message = OutMessage(chat_id=chat_id, text=text)
            sender_bot.send_message_sync(message=message)

        with db.get_session() as session:
            task.last_checked_at_utc = datetime.datetime.utcnow()
            task.next_run_at_utc = datetime.datetime.utcnow() + datetime.timedelta(minutes=3)
            session.add(task)
            session.commit()
    finally:
        with db.get_session() as session:
            task = session.get(SearchTask, task_id)
            task.queued = False
            session.add(task)
            session.commit()


@celery.task
def scan_for_expired():
    with db.get_session() as session:
        statement = select(SearchTask).where(
            SearchTask.active, SearchTask.next_run_at_utc < datetime.datetime.utcnow(), SearchTask.queued == False
        )
        tasks = session.exec(statement)
        if tasks is None:
            return
        for task in tasks:
            run_task.delay(task.id)
            task.queued = True
            session.add(task)
        session.commit()


def get_close_campsite(task: SearchTask, max_distance: int = 15):
    results = get_availability(task.location, task.start_date, task.end_date)
    results = [res for res in results if res.get('distance_miles', 1000) < max_distance]
    return results
