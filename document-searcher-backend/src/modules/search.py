from modules.databases import PostgreSQLConnection
from model_registry import get_model
from modules.scrappers import SinaleviScrapper
from datetime import datetime, timedelta, timezone
import os

def document_search(query_text: str, topic: str, format: str, limit: int = 5):
    db = PostgreSQLConnection()
    model = get_model()
    q_emb = model.encode([query_text], normalize_embeddings=True)[0]
    pgscheme = os.getenv("PGSCHEME")
    items = []

    # Build pgvector literal (compact & safe)
    def _fmt(x: float) -> str:
        if abs(x) < 1e-12:
            x = 0.0
        return f"{float(x):.6f}"
    vec_lit = "[" + ",".join(_fmt(float(v)) for v in q_emb.tolist()) + "]"

    min_similarity = 0.50 # The higher it is the more strict it will be, max is 1
    max_distance = 1.0 - min_similarity

    limit = int(limit)
    sql = f"""
        WITH q(vec) AS (VALUES ('{vec_lit}'::vector)),
        doc_hits AS (
            SELECT t.id, MIN(t.vector <=> q.vec) AS min_distance
            FROM {pgscheme}.{topic} AS t
            CROSS JOIN q
            GROUP BY t.id
            HAVING MIN(t.vector <=> q.vec) < {max_distance}
        ),
        top_docs AS (
            SELECT id, min_distance
            FROM doc_hits
            ORDER BY min_distance
            LIMIT {limit}
        )
        SELECT
            t.id,
            t.chunk_id,
            t.title,
            t.content,
            t.content_hash,
            (t.vector <=> q.vec)  AS distance,
            td.min_distance       AS doc_distance
        FROM {pgscheme}.{topic} AS t
        JOIN top_docs td USING (id)
        CROSS JOIN q
        ORDER BY td.min_distance, t.id, t.chunk_id;
        """

    res = db.fetch_all(sql)
    if isinstance(res, dict) and "error" in res:
        return [{"error": res["error"]}]

    rows = (res or {}).get("rows", [])
    
    for idx, r in enumerate(rows, 1):
        content = (r.get("content") or "").strip()
        title = (r.get("title") or "").strip()
        
         # Look for an existing item with the same title
        existing = next((item for item in items if item["name"] == title), None)

        if existing:
            existing["content"] += " " + content
        else:
            items.append({
                "id": idx,
                "name": title,
                "content": content
            })
    return items

def sinalevi_search(query_text: str, pages: int, format: str) -> str:
    result = {
        "source" : "DocumentSearcher",
        "query" : query_text,
        "limit" : pages,
        "timestamp" : datetime.now(timezone.utc).isoformat(),
        "items" : []
    }

    arguments = [
        "--no-sandbox",
        "--headless=new",
        "--log-level=3",
        "--silent-debugger-extension-api",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-crash-reporter",
        "--disable-infobars",
        "--disable-notifications",
        "--disable-features=Translate,BackForwardCache,UseChromeOSDirectVideoDecoder",
        "--window-size=1365,768",
        "--lang=es-CR",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
        "--disable-blink-features=AutomationControlled",
    ]

    experimentals = {
        "excludeSwitches": ["enable-automation", "enable-logging"],
        "useAutomationExtension": False,
    }

    sinalevi = SinaleviScrapper(arguments, experimentals)
    items = sinalevi.scrappe_website(query_text, pages)
    result["items"] = items
    return result
