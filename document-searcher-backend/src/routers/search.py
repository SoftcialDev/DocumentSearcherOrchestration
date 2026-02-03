from fastapi import APIRouter, Request, Depends
from datetime import datetime, timezone
from modules.authenticators import verify_entra_token
from modules.licenses import require_license_api
from modules.databases import PostgreSQLConnection
from modules.authenticators import get_secret
from modules.scrappers import SinaleviScrapper
from model_registry import get_model
from datetime import datetime, timezone

router = APIRouter(prefix="/api/search", tags=["admin"])

def document_search(query_text: str, topic: str, format: str, limit: int = 5):
    db = PostgreSQLConnection()
    model = get_model()
    q_emb = model.encode([query_text], normalize_embeddings=True)[0]
    pgscheme = get_secret("PGSCHEME")
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
            SELECT t.item_id, MIN(t.vector <=> q.vec) AS min_distance
            FROM {pgscheme}.{topic} AS t
            CROSS JOIN q
            GROUP BY t.item_id
            HAVING MIN(t.vector <=> q.vec) < {max_distance}
        ),
        top_docs AS (
            SELECT item_id, min_distance
            FROM doc_hits
            ORDER BY min_distance
            LIMIT {limit}
        )
        SELECT
            t.item_id,
            t.chunk_id,
            t.title,
            t.content,
            t.content_hash,
            (t.vector <=> q.vec)  AS distance,
            td.min_distance       AS doc_distance
        FROM {pgscheme}.{topic} AS t
        JOIN top_docs td USING (item_id)
        CROSS JOIN q
        ORDER BY td.min_distance, t.item_id, t.chunk_id;
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

@router.get("/search/documents")
#@require_license_api(action="QUERY")
async def documents_seach(req: Request, user=Depends(verify_entra_token())):
    query = req.query_params.get("query")
    topic_list = req.query_params.get("topic")
    format = req.query_params.get("pages", "json")

    topics = topic_list.split(",")

    result = {
        "source" : "DocumentSearcher",
        "query" : query,
        "limit" : 5,
        "timestamp" : datetime.now(timezone.utc).isoformat(),
        "items" : []
    }

    for topic in topics:
        result["items"].extend(document_search(query, topic, format))

    return result

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

@router.get("/search/sinalevi")
#@require_license_api(action="QUERY")
async def sinalevi_scrapper_search(req: Request, user=Depends(verify_entra_token())):
    query = req.query_params.get("query")
    pages = req.query_params.get("pages")
    format = req.query_params.get("format", "json")
    
    return sinalevi_search(query, int(pages), format)

def web_search():
    return "NOT IMPLEMENTED YET"

@router.get("/search/web")
#@require_license_api(action="QUERY")
async def web_scrapper_search(req: Request):
    return web_search()