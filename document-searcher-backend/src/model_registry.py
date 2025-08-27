from sentence_transformers import SentenceTransformer
import threading

_model = None
_lock = threading.Lock()

def set_model(m: SentenceTransformer) -> None:
    global _model
    _model = m

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _lock:
            if _model is None:  # lazy init (per process)
                _model = SentenceTransformer("all-mpnet-base-v2")
    return _model