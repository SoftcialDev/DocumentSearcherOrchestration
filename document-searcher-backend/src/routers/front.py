from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response
from modules.authenticators import get_secret, get_entra_token
import json

router = APIRouter(prefix="/api/front", tags=["admin"])

@router.post("/oauth/token")
async def token():
    return get_entra_token()

@router.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"

router.get("/app-config.js")
def app_config_js():
    MSALCLIENTID = get_secret("MSALCLIENTID")
    MSALTENANTID = get_secret("MSALTENANTID")
    MSALAUTHORITY = f"https://login.microsoftonline.com/{MSALTENANTID}"
    data = {
        "msalClientId": MSALCLIENTID,
        "msalAuthority": MSALAUTHORITY,
    }
    body = "window.__APP_CONFIG__ = " + json.dumps(data) + ";"
    return Response(body, media_type="application/javascript")