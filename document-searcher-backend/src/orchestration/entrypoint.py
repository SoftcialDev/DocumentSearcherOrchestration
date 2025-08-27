from modules.databases import PostgreSQLConnection
from sentence_transformers import SentenceTransformer
from modules import authenticators
from modules import sequences
from datetime import datetime
from zoneinfo import ZoneInfo
from multiprocessing import Process, Queue
from typing import Any, Dict, Iterable
import os
import threading
import time
import logging

PGSCHEME = os.getenv("PGSCHEME")
VECTORIZER_FLAG = True

########################
# Vectorizer threading #
########################
def process_source(task: Dict[str, Any]) -> None:
    composite = task.get("id", None)
    source = task.get("site", None)
    topic = task.get("topic", None)
    if composite and source and topic:
        if source == "Sharepoint":
            sequences.start_sharepoint_sequence(composite, topic)
        elif source == "Onedrive":
            pass
        

def _worker(task_q: Queue) -> None:
    while True:
        item = task_q.get()
        if item is None:   # sentinel → exit
            break
        try:
            process_source(item)
        except Exception:
            logging.exception("Source processing failed")


def run_in_processes(tasks: Iterable[Dict[str, Any]], max_workers: int = 3) -> None:
    task_q: Queue = Queue(maxsize=100)

    # start workers
    workers = [Process(target=_worker, args=(task_q,)) for _ in range(max_workers)]
    for p in workers:
        p.start()

    # enqueue tasks
    for t in tasks:
        task_q.put(t)

    # send sentinel to each worker
    for _ in workers:
        task_q.put(None)

    # wait for completion
    for p in workers:
        p.join()

def vectorizer(schedule):
    pgsql = PostgreSQLConnection()
    query = f"SELECT * FROM public.sources WHERE schedule = '{schedule}'"
    results = pgsql.fetch_all(query)["rows"]
    tasks = [
        {
            "topic": r["topic"] if isinstance(r, dict) else r[0],
            "name":  r["name"]  if isinstance(r, dict) else r[1],
            "id":    r["id"]    if isinstance(r, dict) else r[2],
            "site":  r["site"]  if isinstance(r, dict) else r[3],
            "schedule": schedule,
        }
        for r in results
    ]
    if tasks:
        logging.info(f"Starting orchestration with {len(tasks)} sources at {schedule}")
        run_in_processes(tasks, max_workers=3)
    else:
        logging.info(f"No topics scheduled at {schedule}")

def run_vectorizer(minutes, func):
    def worker():
        global VECTORIZER_FLAG
        while VECTORIZER_FLAG:
            try:
                tz_name="America/Costa_Rica"
                tz = ZoneInfo(tz_name)
                now = datetime.now(tz)
                schedule = str(now.hour * 100 + (30 if now.minute >= 30 else 0))
                func(schedule)
            except Exception:
                logging.exception("Background task raised an exception")
            time.sleep(minutes * 60)

    t = threading.Thread(target=worker, daemon=True)
    t.start()

def switch_vectorizer(status: bool):
    global VECTORIZER_FLAG
    VECTORIZER_FLAG = status


##############
# Entrypoint #
##############
def start_orchestration():
    run_vectorizer(30, vectorizer)