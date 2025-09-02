from modules.databases import PostgreSQLConnection
from model_registry import get_model
import os

def document_search(query_text: str, topic: str,  k: int = 5):
    # Loads the required varaibles
    result = []
    db = PostgreSQLConnection()
    model = get_model()
    q_emb = model.encode([query_text], normalize_embeddings=True)[0]
    pgscheme = os.getenv("PGSCHEME")

    # Build pgvector literal (compact & safe)
    def _fmt(x: float) -> str:
        if abs(x) < 1e-12:
            x = 0.0
        return f"{float(x):.6f}"
    vec_lit = "[" + ",".join(_fmt(float(v)) for v in q_emb.tolist()) + "]"

    min_similarity = 0.50 # The higher it is the more strict it will be, max is 1
    max_distance = 1.0 - min_similarity

    k = int(k)
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
            LIMIT {k}
        )
        SELECT
            t.id,
            t.chunk_id,
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
        title = next((ln.strip() for ln in content.splitlines() if ln.strip()), "")[:120]
        
        result.append({
            "id": idx,
            "name": title,
            "date": "",
            "content": content,
            "source": "Sinalevi"
        })
    return result

def sinalevi_search():
    pass