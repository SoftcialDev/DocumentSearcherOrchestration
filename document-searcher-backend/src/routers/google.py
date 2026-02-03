from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from modules.databases import PostgreSQLConnection
from modules.authenticators import get_secret
import os, time, secrets, base64, hashlib, requests

router = APIRouter(prefix="/api/google", tags=["admin"])

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SCOPE = os.getenv("GOOGLE_SCOPE")
GOOGLE_AUTHZ = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"

PENDING = {}

# ---------- Process helpers ----------
def mk_code_verifier():
    return base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode()

def mk_code_challenge(verifier: str):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

# ---------- DB helpers ----------
def collect_token(user_id: str) -> dict:
    """
    TODO: implement: fetch the latest tokens for this user from DB.
    Must return a dict with keys: access_token, refresh_token, expires_at (int epoch seconds).
    Example:
      return {"access_token": "...", "refresh_token": "...", "expires_at": 1731350400}
    """
    postgresql = PostgreSQLConnection()
    pgscheme = get_secret("PGSCHEME")

    query = f"""SELECT access_token, refresh_token, expires_at 
        FROM {pgscheme}.connected_accounts
        WHERE user_id = '{user_id}'
    """

    result = postgresql.fetch_all(query)
    rows = result.get("rows")

    if rows and len(rows) > 0:
        return rows[0]
    return None

def store_tokens(user_id: str, data: dict):
    postgresql = PostgreSQLConnection()
    pgscheme = get_secret("PGSCHEME")
    query = f"""
        INSERT INTO {pgscheme}.connected_accounts
            (user_id, source, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, source) DO UPDATE
        SET access_token = EXCLUDED.access_token,
            expires_at   = EXCLUDED.expires_at,
            -- keep the existing refresh_token if the new one is NULL/absent
            refresh_token = COALESCE(EXCLUDED.refresh_token, {pgscheme}.connected_accounts.refresh_token)
    """
    records = []
    insert = (
        user_id, 
        "GoogleDrive", 
        data.get("access_token"), 
        data.get("refresh_token"),
        int(time.time()) + int(data.get("expires_in", 3600)) - 30
    )
    records.append(insert)
    postgresql.execute_many(query, records)
    return data


def refresh_access_token(user_id: str):
    rec = collect_token(user_id)
    rt = rec.get("refresh_token")
    if not rt:
        raise HTTPException(status_code=400, detail="No refresh_token stored")
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": rt,
        "grant_type": "refresh_token",
    }
    r = requests.post(GOOGLE_TOKEN, data=payload, timeout=15)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Refresh error: {r.text}")
    data = r.json()
    token = store_tokens(user_id, data)
    return token

def get_valid_access_token(user_id: str):
    rec = collect_token(user_id)
    if rec.get("access_token") and rec.get("expires_at", 0) > int(time.time()):
        return rec["access_token"]
    return refresh_access_token(user_id)

# ---------- Backend helpers ----------

@router.get("/oauth/start")
def google_oauth_start(return_to: str = "/", user_hint: str = ""):
    """
    Redirect the user to Google's consent screen using Authorization Code + PKCE.
    You should map this request to your logged-in user. Here we just demo user_id="u1".
    """

    state = secrets.token_urlsafe(24)
    code_verifier = mk_code_verifier()
    code_challenge = mk_code_challenge(code_verifier)

    PENDING[state] = {"code_verifier": code_verifier, "return_to": return_to, "user_id": user_hint}

    query = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",                 
        "include_granted_scopes": "true",
        "prompt": "consent",                      # force refresh_token on first connect
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return RedirectResponse(url=f"{GOOGLE_AUTHZ}?{urlencode(query)}", status_code=302)

@router.get("/oauth/callback")
def google_oauth_callback(code: str, state: str):
    ctx = PENDING.pop(state, None)
    if not ctx:
        raise HTTPException(status_code=400, detail="Invalid state")
    code_verifier = ctx["code_verifier"]
    user_id = ctx["user_id"]
    # Exchange code for tokens
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post(GOOGLE_TOKEN, data=data, timeout=15)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Token exchange error: {r.text}")
    token_payload = r.json()
    store_tokens(user_id, token_payload)
    return_to = ctx.get("return_to") or "/"
    return RedirectResponse(url=return_to, status_code=302)

# ---------- Frontend helpers ----------
@router.get("/access-token")
def google_access_token():
    """Return a valid short-lived access token and its expiry for the current user."""
    user_id = "daniel.villanueva@softcial.onmicrosoft.com"  # TODO: derive from your own session/JWT
    token = get_valid_access_token(user_id)
    # re-read for current expiry after potential refresh
    rec = collect_token(user_id)
    return {"access_token": token, "expires_at": rec.get("expires_at")}

# Example: scheduled job uses refresh token directly, no browser needed
@router.get("/sync-now")
def google_sync_now():
    user_id = "u1"
    token = get_valid_access_token(user_id)
    return {"ok": True}