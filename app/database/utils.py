from typing import List, Optional

from sqlmodel import select
from sqlmodel.engine.result import ScalarResult
from tabulate import tabulate

from .database import Database
from .models import SearchTask


def clear_queued(db: Database):
    with db.get_session() as session:
        results = session.exec(select(SearchTask).where(SearchTask.queued == True))
        for task in results:
            task.queued = False
            session.add(task)
        session.commit()


def get_task_representation(task: SearchTask) -> List[Optional[str]]:
    last_checked = task.last_checked_at_utc.strftime('%H:%M') if task.last_checked_at_utc else None
    row = [str(task.active_id), task.location, task.start_date.strftime('%m/%d'), task.end_date.strftime('%m/%d'),
           last_checked]
    return row


def get_task_summary(task: SearchTask) -> str:
    row = get_task_representation(task)
    row = [el for el in row if el]
    return ' '.join(row)


def get_task_tabulate(results: ScalarResult[SearchTask]):
    headers = ['id', 'location query', 'start date', 'end date', 'checked (utc)']
    table = []
    for task in results:
        row = get_task_representation(task)
        table.append(row)
    return tabulate(table, headers=headers, tablefmt="plain")
