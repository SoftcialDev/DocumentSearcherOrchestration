from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_pool, close_pool
from routers import client, admin 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_pool()
    yield
    # Shutdown
    await close_pool()

app = FastAPI(title="License Service", lifespan=lifespan)

# Routers
app.include_router(client.router)
app.include_router(admin.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "http://localhost:8000", "http://127.0.0.1:3000", "https://documentsearcher.softcial.com"],  # or ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", "8000"))  # Azure Container Apps often sets PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)