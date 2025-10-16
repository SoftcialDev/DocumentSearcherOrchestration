# This module usage is to collect and authenticate services within Azure

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from functools import lru_cache
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import msal, requests, os, time, httpx, threading

bearer_scheme = HTTPBearer(auto_error=False)

##########################
# Sources Authentication #
##########################
def get_sharepoint_token(logs: list):

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    body = {
        "client_id": get_secret("SHAREPOINTENTRACLIENTID"),
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": get_secret("SHAREPOINTENTRASECRET"),
        "grant_type": "client_credentials"
    }
    ONEDRIVEENTRATENANT = get_secret("ONEDRIVEENTRATENANT")
    GRAPH_TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{ONEDRIVEENTRATENANT}/oauth2/v2.0/token"

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

    ONEDRIVEENTRATENANT = get_secret("ONEDRIVEENTRATENANT")
    ONEDRIVEENTRACLIENTID = get_secret("ONEDRIVEENTRACLIENTID")
    AUTHORITY = f"https://login.microsoftonline.com/{ONEDRIVEENTRATENANT}"
    SCOPE = ["https://graph.microsoft.com/.default"]  # Application permission scope

    app = msal.ConfidentialClientApplication(
        ONEDRIVEENTRACLIENTID,
        authority=AUTHORITY,
        client_credential=get_secret("ONEDRIVEENTRASECRET")
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
    MSALTENANTID = get_secret("MSALTENANTID")
    url = f"https://login.microsoftonline.com/{MSALTENANTID}/v2.0/.well-known/openid-configuration"
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
    
    MSALCLIENTID = get_secret("MSALCLIENTID")
    MSALTENANTID = get_secret("MSALTENANTID")
    MSALSECRET = get_secret("MSALSECRET")
    MSALIDURI = f"api://botid{MSALCLIENTID}"

    cca = msal.ConfidentialClientApplication(
        MSALCLIENTID,
        authority=f"https://login.microsoftonline.com/{MSALTENANTID}",
        client_credential=MSALSECRET,
    )

    result = cca.acquire_token_for_client(scopes=[f"{MSALIDURI}/.default"])
    token = result["access_token"]
    return token 

def verify_entra_token():
    def _dep(request: Request):
        MSALTENANTID = get_secret("MSALTENANTID")
        MSALCLIENTID =  get_secret("MSALCLIENTID")
        MSALIDURI = f"api://botid{MSALCLIENTID}"
        ENTRA_ALLOWED_ISSUER = {f"https://sts.windows.net/{MSALTENANTID}/", f"https://login.microsoftonline.com/{MSALTENANTID}/v2.0"}

        ALLOWED_AUDS = {MSALCLIENTID, MSALIDURI}
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
        if tid != MSALTENANTID or iss not in ENTRA_ALLOWED_ISSUER:
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

################
# Secrets Auth #
################
class SecretStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._kv_uri = os.getenv("KEY_VAULT_URI")
        self._cred = DefaultAzureCredential()
        self._client = SecretClient(vault_url=self._kv_uri, credential=self._cred)
        self._cache = {}  # name -> {"v": value, "t": timestamp}
        self._ttl = int(os.getenv("SECRETS_TTL_SECONDS", "1800"))
        self._cache_lock = threading.Lock()

    def get(self, name: str) -> str:
        now = time.time()
        # fetch from cache
        with self._cache_lock:
            item = self._cache.get(name)
            if item and (now - item["t"] < self._ttl):
                return item["v"]

        # fetch latest from Key Vault if TTL expired
        val = self._client.get_secret(name).value
        with self._cache_lock:
            self._cache[name] = {"v": val, "t": now}
        return val

def get_secret(name: str) -> str:
    return SecretStore().get(name)