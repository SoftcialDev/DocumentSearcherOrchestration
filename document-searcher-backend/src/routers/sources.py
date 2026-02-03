from fastapi import APIRouter, UploadFile, Request, File, Form, Depends
from fastapi.responses import JSONResponse
from orchestration.entrypoint import file_refresh
from modules.authenticators import get_secret, verify_entra_token
from modules.logs import write_line
from modules import databases
from pathlib import Path
import re

router = APIRouter(prefix="/api/sources", tags=["admin"])

PGSCHEME = get_secret("PGSCHEME")
UPLOAD_DIR = Path("/tmp/uploads")

@router.get("/list-sources")
async def list_sources(req: Request, user=Depends(verify_entra_token())):
    topic = req.query_params.get("topic")
    pgsql = databases.PostgreSQLConnection()
    query = f"SELECT * FROM {PGSCHEME}.sources WHERE topic = '{topic}'"
    return pgsql.fetch_all(query)['rows']


@router.post("/add-source")
async def add_source(req: Request, user=Depends(verify_entra_token())):

    def compose_ids(s, site: str) -> str:
        if site == "GoogleDrive":
            return s["sharepoint_item"]
        return f"{s['sharepoint_site']},{s['sharepoint_list']},{s['sharepoint_item']}"

    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

    print(data)
    topic = data.get("topic")
    sources = data.get("sources")
    account_source = data.get("account_source")
    site = data.get("site", "Sharepoint")


    if not topic or not isinstance(sources, list):
        return JSONResponse(
            {"status": "error", "message": "Missing or invalid parameter(s): topic and/or sources"},
            status_code=400,
        )

    # Ensure required keys exist in each source item
    required = {"name", "sharepoint_site", "sharepoint_list", "sharepoint_item"}
    missing_idx = [
        i for i, s in enumerate(sources)
        if not isinstance(s, dict) or not required.issubset(s.keys())
    ]
    if missing_idx:
        return JSONResponse(
            {
                "status": "error",
                "message": f"Each source must include {sorted(required)}. "
                           f"Issue at index(es): {missing_idx}"
            },
            status_code=400,
        )

    values = [
        (
            topic,
            s["name"],
            compose_ids(s, site),
            "0100",  # Default 1 AM
            site,
        )
        for s in sources
    ]

    try:
        # Insert values into their own source table
        pgsql = databases.PostgreSQLConnection()
        query = f"""
            INSERT INTO {PGSCHEME}.sources (topic, name, id, schedule, site)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (topic, id) DO NOTHING;
        """
        pgsql.execute_many(query, values)

        # If the source is also GoogleDrive, links where it came from
        if site == "GoogleDrive":
            connection_query = f"""
                INSERT INTO {PGSCHEME}.sources_accounts (topic, id, user_id, account_source)
                VALUES (%s, %s, %s, %)
                ON CONFLICT (topic, id, user_id, account_source) DO NOTHING;
            """
            connection_values = [
                (
                    topic,
                    compose_ids(s, site),
                    "email",
                    site, 
                )
                for s in sources
            ]

            pgsql.execute_many(connection_query, connection_values)
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Failed to add sources: {e}"},
            status_code=500,
        )

    return {"status": "success", "message": f"{len(values)} source(s) added/kept"}

@router.delete("/remove-source")
async def remove_source(req: Request, user=Depends(verify_entra_token())):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

    topic_name = data.get("topic_name")
    source_id = data.get("source_id")

    # Optional: fallback to query params if body missing
    if topic_name is None:
        topic_name = req.query_params.get("topic_name")
    if source_id is None:
        source_id = req.query_params.get("source_id")

    if topic_name is None or source_id is None:
        return JSONResponse(
            {"status": "error", "message": "Missing parameter: topic_name and/or source_id not specified"},
            status_code=400,
        )

    result_vectors = result_manifests = result_sources = False
    try:
        pgsql = databases.PostgreSQLConnection()
        parent_id = source_id.rsplit(",", 1)[-1].strip()
            
        # Start deleting
        query_sources = f"""
            DELETE FROM {PGSCHEME}.sources WHERE topic = '{topic_name}' AND id = '{source_id}'
        """
        result_sources = pgsql.execute_one(query_sources)
        write_line(query_sources)

        query_vectors = f"""
            DELETE FROM {PGSCHEME}.{topic_name} WHERE drive_id = '{parent_id}'
        """
        result_vectors = pgsql.execute_one(query_vectors)
        write_line(query_vectors)

        query_manifests = f"""
            DELETE FROM {PGSCHEME}.manifests WHERE drive_id = '{parent_id}' AND topic = '{topic_name}'
        """
        result_manifests = pgsql.execute_one(query_manifests)
        write_line(query_manifests)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    if result_sources and result_manifests and result_vectors:
        return {"status": "success", "message": "Source removed successfully"}
    else:
        return JSONResponse({"status": "error", "message": ""}, status_code=500)
    

@router.patch("/update-source")
async def update_source(req: Request, user=Depends(verify_entra_token())):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

    topic = data.get("topic")
    source_id = data.get("id")
    schedule = data.get("schedule")

    if not topic or source_id is None or not schedule:
        return JSONResponse(
            {"status": "error", "message": "Missing parameter: topic, id and/or schedule not specified"},
            status_code=400,
        )

    pgsql = databases.PostgreSQLConnection()
    query = f"UPDATE {PGSCHEME}.sources SET schedule = {schedule} WHERE topic = '{topic}' AND id = '{id}'"
    if  pgsql.execute_one(query):
        return {"status": "success", "message": "Source schedule updated"}
    else:
        return JSONResponse({"status": "error", "message": "Could not update source"}, status_code=500)

@router.post("/upload-source")
async def upload_source(
        topic: str = Form(...), 
        file: UploadFile = File(...), 
        user=Depends(verify_entra_token())
    ):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9._-]+', '_', file.filename)
    dest = UPLOAD_DIR / safe_name

    # Write file locally
    try:
        with open(dest, "wb") as buffer:
            while content := await file.read(1024):  # Read in chunks
                buffer.write(content)
    finally:
        await file.close()

    # Execute manual refresh for the uploaded file
    # t = threading.Thread(target=file_refresh, args=(topic, dest, safe_name), daemon=True)
    # t.start()
    file_refresh(topic, dest, safe_name)

    return JSONResponse({"status": "success", "message": "File uploaded"})
