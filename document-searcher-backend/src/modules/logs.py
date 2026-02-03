# Logs.py
from datetime import datetime, timezone
from typing import Iterable
import os, threading, logging

# Default log path (can be changed via set_log_path)
PATH = "logs.txt"

# Internal state, prevents other threads from writing
_file_lock = threading.Lock()

def write_line(line: str, console=True) -> None:
    """
    Write a single line of string in the logs.
    Used when interleaving is not a problem.
    """
    if not line:
        # Skip empty content
        return
    
    with _file_lock:
        with open(PATH, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}]" + line + "\n")
            
    if console:
        logging.info(f"{line}")


def write_block(records: list[str] | Iterable[str], trigger: str, console=True) -> None:
    """
    Write a whole block a lock.
    Used when interleaving needs to be avoided.
    """
    if not list:
        # Skip empty content
        return
    
    ts = datetime.now(timezone.utc).isoformat()
    # Build one chunk to avoid partial interleaving
    lines = [f"[{datetime.now():%Y-%m-%d %H:%M:%S}]", *(str(s) for s in records), ""]
    chunk = "\n" + "\n".join(lines) + "\n"

    with _file_lock:
        with open(PATH, "a", encoding="utf-8", newline="\n") as f:
            f.write(chunk)
            
    if console:
        logging.info(f"{chunk}")


def clean_logs() -> None:
    """Truncate the log file safely (creates it if missing)."""
    with _file_lock:
        # Ensure file exists, then truncate to 0
        open(PATH, "a", encoding="utf-8").close()
        os.truncate(PATH, 0)
