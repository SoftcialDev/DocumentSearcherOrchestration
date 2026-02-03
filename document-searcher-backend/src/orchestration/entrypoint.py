from modules.databases import PostgreSQLConnection
from modules.logs import write_line, write_block
from modules.sequences import local, sharepoint, googledrive
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from multiprocessing import Process, Queue
from typing import Any, Dict, Iterable
import os, threading, time, logging, uuid


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
            sharepoint.start_sharepoint_sequence(composite, topic)
        elif source == "Onedrive":
            pass
        elif source == "Google":
            googledrive.start_googledrive_sequence()
        

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
    results = pgsql.fetch_all(query)
    if not results:
        logging.error(f"Orchestration at {schedule} aborted...")
        return
    rows = results["rows"]
    tasks = [
        {
            "topic": r["topic"] if isinstance(r, dict) else r[0],
            "name":  r["name"]  if isinstance(r, dict) else r[1],
            "id":    r["id"]    if isinstance(r, dict) else r[2],
            "site":  r["site"]  if isinstance(r, dict) else r[3],
            "schedule": schedule,
        }
        for r in rows
    ]
    if tasks:
        write_line(f"Starting orchestration with {len(tasks)} sources at {schedule}")
        run_in_processes(tasks, max_workers=3)
    else:
        write_line(f"No topics scheduled at {schedule}")

def run_vectorizer(func):
    def worker():
        global VECTORIZER_FLAG
        tz = ZoneInfo("America/Costa_Rica")
        while VECTORIZER_FLAG:
            try:
                now = datetime.now(tz)

                # round up to the next 00 or 30 minute mark
                minute_block = 0 if now.minute < 30 else 30
                # next target is either the current hour’s :30 or the next hour’s :00
                if minute_block == 0:
                    next_run = now.replace(minute=30, second=0, microsecond=0)
                else:
                    next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

                # compute schedule string for *this* run (based on current clock)
                schedule = str(now.hour * 100 + (30 if now.minute >= 30 else 0))
                func(schedule)

            except Exception as e:
                logging.exception("Background task raised an exception")

            # sleep until the next boundary
            sleep_seconds = (next_run - datetime.now(tz)).total_seconds()
            write_line(f"Waiting {sleep_seconds} for next iteration")
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    t = threading.Thread(target=worker, daemon=True)
    t.start()

def switch_vectorizer(status: bool):
    global VECTORIZER_FLAG
    VECTORIZER_FLAG = status

def manual_refresh(topic_name):
    write_line(f"Starting manual refresh of topic {topic_name}")
    pgsql = PostgreSQLConnection()
    query = f"""
        SELECT id
        FROM public.sources
        WHERE topic = '{topic_name}'
    """
    results = pgsql.fetch_all(query)
    rows = results["rows"]
    for r in rows:
        composite = r["id"] if isinstance(r, dict) else r[0]
        sharepoint.start_sharepoint_sequence(composite, topic_name)

def file_refresh(topic, file_path, file_name):
    file_id = str(uuid.uuid4())
    local.start_local_sequence(file_path, file_name, file_id, topic)
    values = [
        (
            topic,
            file_name,
            file_id,
            "0100",
            file_id,
        ),
    ]
    # sources.add_sources(values)

##############
# Entrypoint #
##############
def start_orchestration():
    run_vectorizer(vectorizer)
    