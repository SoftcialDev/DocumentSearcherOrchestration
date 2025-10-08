from modules.logs import write_block, write_line
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from functools import lru_cache
import msal, requests, os, time, httpx

bearer_scheme = HTTPBearer(auto_error=False)

# Sharepoint Authentication
SHAREPOINT_ENTRA_SECRET_VALUE = os.getenv("SHAREPOINT_ENTRA_SECRET_VALUE")
SHAREPOINT_ENTRA_CLIENT_ID = os.getenv("SHAREPOINT_ENTRA_CLIENT_ID")

# Onedrive Authentication
ONEDRIVE_ENTRA_SECRET_VALUE = os.getenv("ONEDRIVE_ENTRA_SECRET_VALUE")
ONEDRIVE_ENTRA_TENANT_ID = os.getenv("ONEDRIVE_ENTRA_TENANT_ID")
ONEDRIVE_ENTRA_CLIENT_ID = os.getenv("ONEDRIVE_ENTRA_CLIENT_ID")

# Graph Authentication
GRAPH_TOKEN_ENDPOINT = os.getenv("GRAPH_TOKEN_ENDPOINT")

# Entra Auth values
ENTRA_ID_URI = os.getenv("ENTRA_ID_URI")
ENTRA_CLIENT_ID = os.getenv("ENTRA_CLIENT_ID")
ENTRA_TENANT_ID = os.getenv("ENTRA_TENANT_ID")
ENTRA_SECRET = os.getenv("ENTRA_SECRET")
ENTRA_ISSUER = os.getenv("ENTRA_ISSUER")
ENTRA_ALLOWED_ISSUER = {f"https://sts.windows.net/{ENTRA_TENANT_ID}/", f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0"}
OPENID_CONFIG_URL = f"{ENTRA_ISSUER}/.well-known/openid-configuration"
ALLOWED_AUDS = {ENTRA_CLIENT_ID, ENTRA_ID_URI}

##########################
# Sources Authentication #
##########################
def get_sharepoint_token(logs: list):

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    body = {
        "client_id": SHAREPOINT_ENTRA_CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": SHAREPOINT_ENTRA_SECRET_VALUE,
        "grant_type": "client_credentials"
    }

    try:
        response = requests.post(GRAPH_TOKEN_ENDPOINT, headers=headers, data=body)
        response.raise_for_status()
        token = response.json()["access_token"]
        return token
    except requests.exceptions.RequestException as e:
        logs.append("---ERROR---")
        logs.append(f"Sharepoint Token request failed: {e}")
        logs.append("---ERROR---")
        return None
    
def get_onedrive_token(logs: list):

    AUTHORITY = f"https://login.microsoftonline.com/{ONEDRIVE_ENTRA_TENANT_ID}"
    SCOPE = ["https://graph.microsoft.com/.default"]  # Application permission scope

    app = msal.ConfidentialClientApplication(
        ONEDRIVE_ENTRA_CLIENT_ID,
        authority=AUTHORITY,
        client_credential=ONEDRIVE_ENTRA_SECRET_VALUE
    )

    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" in result:
        token = result["access_token"]
        return token
    else:
        logs.append("---ERROR---")
        logs.append(f"Onedrive Token request failed: {result.get('error_description')}")
        logs.append("---ERROR---")
        return None


######################
# API Authentication #
######################
@lru_cache(maxsize=1)
def _get_openid_config():
    url = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0/.well-known/openid-configuration"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()

@lru_cache(maxsize=1)
def _get_jwks():
    jwks_uri = _get_openid_config()["jwks_uri"]
    resp = httpx.get(jwks_uri, timeout=10)
    resp.raise_for_status()
    return resp.json()

def _get_token_from_header(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    return auth.split(" ", 1)[1]

def get_entra_token():
    cca = msal.ConfidentialClientApplication(
        ENTRA_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}",
        client_credential=ENTRA_SECRET,
    )

    result = cca.acquire_token_for_client(scopes=[f"{ENTRA_ID_URI}/.default"])
    token = result["access_token"]
    return token 

def verify_entra_token():
    def _dep(request: Request):
        token = _get_token_from_header(request)
        jwks = _get_jwks()

        try:
            headers = jwt.get_unverified_header(token)
            key = next((k for k in jwks["keys"] if k.get("kid") == headers.get("kid")), None)
            if not key:
                raise HTTPException(status_code=401, detail="Invalid token key")

            # Let python-jose verify signature only; we’ll validate aud/iss ourselves.
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                options={
                    "verify_aud": False,  # we'll check manually
                    "verify_iss": False,  # we'll check manually
                    "verify_at_hash": False,
                },
            )
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

        # exp
        if claims.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")

        # tenant & issuer
        tid = claims.get("tid")
        iss = claims.get("iss")
        if tid != ENTRA_TENANT_ID or iss not in ENTRA_ALLOWED_ISSUER:
            raise HTTPException(status_code=401, detail="Invalid issuer/tenant")

        # audience (accept GUID or URI)
        aud = claims.get("aud")
        # aud can be list or str
        aud_set = set(aud if isinstance(aud, list) else [aud])
        if not (aud_set & ALLOWED_AUDS):
            raise HTTPException(status_code=401, detail="Invalid audience")

        # SKIP scopes entirely (no `scp` check). App-only tokens won’t have them.
        return claims

    return _dep