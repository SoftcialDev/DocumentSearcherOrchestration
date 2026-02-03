from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from orchestration.entrypoint import manual_refresh
from modules.authenticators import get_secret, verify_entra_token
from modules.licenses import require_license_api
from modules import databases
import re, threading

router = APIRouter(prefix="/api/topics", tags=["admin"])

PGSCHEME = get_secret("PGSCHEME")
RESERVED_TABLES = ["sources", "topics", "manifests"]

@router.get("/list-topics")
async def list_topics(user=Depends(verify_entra_token())):
    pgsql = databases.PostgreSQLConnection()
    query = f"SELECT name FROM {PGSCHEME}.topics"
    result = pgsql.fetch_all(query)
    raw = result["rows"]
    return JSONResponse(content=raw, status_code=200)


@router.post("/create-topic")
# @require_license_api(action="CREATE-TOPIC")
async def create_topic(req: Request, user=Depends(verify_entra_token())):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)
    
    topic_name = data.get("topic_name", "")

    if not topic_name:
        return JSONResponse({"status": "error", "message": f"Missing or blank parameter 'topic_name'"},status_code=400,)

    topic_name = topic_name.lower()
    topic_name = topic_name.replace(" ", "_")
    topic_name = re.sub(r'[^a-z0-9_]', '', topic_name)

    if topic_name.lower() in RESERVED_TABLES:
        return JSONResponse(
            {"status": "error", "message": f"'{topic_name}' is a reserved name"},
            status_code=400,
        )

    ok = False

    pgsql = databases.PostgreSQLConnection()
    query = f"""CREATE TABLE {PGSCHEME}.{topic_name} (
        item_id text,
        drive_id text,
        chunk_id integer,
        title text,
        content text,
        content_hash text,
        vector vector(768),
        tsv tsvector GENERATED ALWAYS AS (to_tsvector('spanish'::regconfig, content)) STORED
    )"""
    result = pgsql.execute_one(query)

    if result:
        # Create a record in the topics table
        query = f"""INSERT INTO {PGSCHEME}.topics VALUES('{topic_name}')"""
        ok = pgsql.execute_one(query)
    if ok:
        return {"status": "success", "message": f"Topic '{topic_name}' created successfully"}
    else:
        return JSONResponse(
            {"status": "error", "message": "The topic already exists"},
            status_code=500,
        )
    

@router.patch("/rename-topic")
async def rename_topic(req: Request, user=Depends(verify_entra_token())):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)
    
    old_name = data.get("old_name")
    new_name = data.get("new_name")

    if not old_name or not new_name:
        return JSONResponse(
            {"status": "error", "message": "Missing parameter(s): old_name and/or new_name not specified"},
            status_code=400,
        )
    
    new_name = re.sub(r'[^a-z0-9_]', '_', new_name)
    if new_name.lower() in RESERVED_TABLES:
        return JSONResponse(
            {"status": "error", "message": f"'{new_name}' is a reserved name"},
            status_code=400,
        )

    ok = False
    pgsql = databases.PostgreSQLConnection()
    # Rename the origin table
    query = f"""ALTER TABLE {PGSCHEME}.{old_name} RENAME TO {new_name}"""
    result = pgsql.execute_one(query)

    if result:
        # Update record from topics table
        query = f"""UPDATE {PGSCHEME}.topics SET name = {new_name} WHERE name = '{old_name}'"""
        ok = pgsql.execute_one(query)
    
    if ok:
        return {"status": "success", "message": f"Topic rename from '{old_name}' to '{new_name}' successfully"}
    else:
        return JSONResponse(
            {"status": "error", "message": f"Could not find topic with the name '{old_name}'"},
            status_code=500,
        )
    

@router.delete("/delete-topic")
async def delete_topic(req: Request, user=Depends(verify_entra_token())):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

    topic_name = data.get("topic_name")

    if topic_name is None:
        return JSONResponse(
            {"status": "error", "message": "Missing parameter: topic_name not specified"},
            status_code=400,
        )

    ok = False
    pgsql = databases.PostgreSQLConnection()
    # Collect the drive_id references
    drive_ids_query = f"""SELECT DISTINCT drive_id FROM {PGSCHEME}.{topic_name}"""
    drive_ids = pgsql.fetch_all(drive_ids_query)

    # Remove the origin table
    drop_query = f"""DROP TABLE {PGSCHEME}.{topic_name}"""
    drop_result = pgsql.execute_one(drop_query)

    if drop_result:
        # Remove record from manifests table
        sources_query = f"""DELETE FROM {PGSCHEME}.manifests WHERE topic = '{topic_name}'"""
        sources_result = pgsql.execute_one(sources_query)
    
        # Remove record from sources table
        manifests_query = f"""DELETE FROM {PGSCHEME}.sources WHERE topic = '{topic_name}'"""
        manifests_result = pgsql.execute_one(manifests_query)

        # Remove record from topics table
        topics_query = f"""DELETE FROM {PGSCHEME}.topics WHERE name = '{topic_name}'"""
        topics_result = pgsql.execute_one(topics_query)

        ok = topics_result and manifests_result and sources_result
    else:
        return False
    if ok:
        return {"status": "success", "message": "Topic deleted successfully"}
    else:
        return JSONResponse(
            {"status": "error", "message": f"Could not find topic with the name '{topic_name}'"},
            status_code=500,
        )

@router.patch("/refresh-topic")
async def refresh_topic(req: Request, user=Depends(verify_entra_token())):
    """

    """
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

    topic = data.get("topic")

    t = threading.Thread(target=manual_refresh, args=(topic,), daemon=True)
    t.start()

    return JSONResponse({"status": "success", "message": "Topic refresh started, please allow some minutes for it to finish"})
