from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import api.sources as api_sources
import api.topics as api_topics
import modules.sources as sources
import re, logging

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # or ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESERVED_TABLES = ["sources", "topics", "manifests"]

####################
# Topics endpoints #
####################
@app.get("/list-topics")
async def list_topics():
    raw = api_topics.list_topics()
    return JSONResponse(content=raw, status_code=200)


@app.post("/create-topic")
async def create_topic(req: Request):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)
    
    topic_name = data.get("topic_name", "")

    if not topic_name:
        return JSONResponse({"status": "error", "message": f"Missing or blank parameter 'topic_name'"},status_code=400,)

    topic_name = re.sub(r'[^a-z0-9_]', '_', topic_name)

    if topic_name.lower() in RESERVED_TABLES:
        return JSONResponse(
            {"status": "error", "message": f"'{topic_name}' is a reserved name"},
            status_code=400,
        )

    ok = api_topics.create_topic(topic_name)
    if ok:
        return {"status": "success", "message": f"Topic '{topic_name}' created successfully"}
    else:
        return JSONResponse(
            {"status": "error", "message": "The topic already exists"},
            status_code=500,
        )
    

@app.patch("/rename-topic")
async def rename_topic(req: Request):
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

    ok = api_topics.rename_topic(old_name, new_name)
    if ok:
        return {"status": "success", "message": f"Topic rename from '{old_name}' to '{new_name}' successfully"}
    else:
        return JSONResponse(
            {"status": "error", "message": f"Could not find topic with the name '{old_name}'"},
            status_code=500,
        )
    

@app.delete("/delete-topic")
async def delete_topic(req: Request):
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

    ok = api_topics.delete_topic(topic_name)
    if ok:
        return {"status": "success", "message": "Topic deleted successfully"}
    else:
        return JSONResponse(
            {"status": "error", "message": f"Could not find topic with the name '{topic_name}'"},
            status_code=500,
        )

#####################
# Sources endpoints #
#####################
@app.get("/list-sources")
async def list_sources(req: Request):
    topic = req.query_params.get("topic")
    return api_sources.list_sources(topic)


@app.post("/add-source")
async def add_source(req: Request):
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Invalid JSON body"}, status_code=400)

    topic = data.get("topic")
    sources = data.get("sources")
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
            f"{s['sharepoint_site']},{s['sharepoint_list']},{s['sharepoint_item']}",
            "0100",  # Default 1 AM
            site,
        )
        for s in sources
    ]

    try:
        api_sources.add_sources(values)
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": f"Failed to add sources: {e}"},
            status_code=500,
        )

    return {"status": "success", "message": f"{len(values)} source(s) added/kept"}

@app.delete("/remove-source")
async def remove_source(req: Request):
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

    try:
        ok = api_sources.remove_source(topic_name, source_id)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    if ok:
        return {"status": "success", "message": "Source removed successfully"}
    else:
        return JSONResponse({"status": "error", "message": ""}, status_code=500)
    

@app.patch("/update-source")
async def update_source(req: Request):
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

    ok = api_sources.update_source(topic, source_id, schedule)
    if ok:
        return {"status": "success", "message": "Source schedule updated"}
    else:
        return JSONResponse({"status": "error", "message": "Could not update source"}, status_code=500)

###########################
# Data Sources collection #
###########################
@app.get("/documents/search")
async def documents_seach(req: Request):
    query = req.query_params.get("query")
    topic = req.query_params.get("topic")
    format = req.query_params.get("pages", "json")
    return sources.get_document_search(query, topic, format)

@app.get("/nexus-scrapper/search")
async def nexus_scrapper_search(req: Request):
    pass

@app.get("/sinalevi-scrapper/search")
async def sinalevi_scrapper_search(req: Request):
    query = req.query_params.get("query")
    pages = req.query_params.get("pages")
    format = req.query_params.get("format", "json")
    
    return sources.get_sinalevi_result(query, int(pages), format)

@app.get("/web-scrapper/search")
async def web_scrapper_search(req: Request):
    pass

def start_server():
    import uvicorn
    uvicorn.run("serverapi:app", host="0.0.0.0", port=5000, reload=True)