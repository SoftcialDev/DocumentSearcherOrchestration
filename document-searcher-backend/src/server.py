from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
load_dotenv()

from fastapi import FastAPI, APIRouter
from fastapi.responses import PlainTextResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from modules.authenticators import get_secret, get_entra_token
from routers import google, sources, topics, search, front

api = APIRouter(prefix="/api")

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo/backend/main.py -> repo/
FRONTEND_BUILD = BASE_DIR / "document-searcher-frontend" / "build"

app = FastAPI()
app.include_router(front.router)
app.include_router(google.router)
app.include_router(search.router)
app.include_router(sources.router)
app.include_router(topics.router)

# Serve React via Python, project must be compiled
app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:3000", "https://documentsearcher.softcial.com"],  # or ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def start_server():
    import uvicorn
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        reload_dirs=[".", "modules"],
        reload_includes=["*.py", "*.env"],
        reload_excludes=["*.pyc", "node_modules/*"],
    )

if __name__ == "__main__":
    start_server()
