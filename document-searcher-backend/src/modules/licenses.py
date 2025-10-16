from fastapi.responses import JSONResponse
from modules.authenticators import get_secret
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from api import topics
from typing import Dict, Any, Optional, Callable
from functools import wraps
import time, requests, base64, jwt, os, json

ISSUER = os.getenv("ISSUER") # collect from .env injected by terraform
JWKS_URL = os.getenv("JWKS_URL") # collect from .env injected by terraform
TOKEN_URL = os.getenv("TOKEN_URL") # collect from .env injected by terraform
MIN_TTL_BUFFER = 300  # renew if <5 min left
CLOCK_SKEW = 5        # tolerate small clock drift

_jwks_cache: Dict[str, Dict[str, Any]] = {}  # kid -> jwk

def _b64url_to_int(b64: str) -> int:
    pad = '=' * (-len(b64) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(b64 + pad), "big")

def _get_key_for_kid(kid: str):
    jwks = requests.get(JWKS_URL, timeout=5).json()
    for k in jwks["keys"]:
        _jwks_cache[k["kid"]] = k
    jwk = _jwks_cache.get(kid)
    if not jwk:
        raise ValueError("kid not found in JWKS")
    n = _b64url_to_int(jwk["n"])
    e = _b64url_to_int(jwk["e"])
    pub_numbers = rsa.RSAPublicNumbers(e, n).public_key()
    return pub_numbers.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def _jwt_exp(token: str) -> int:
    try:
        _, payload_b64, _ = token.split(".")
        payload = json.loads(_b64url_decode(payload_b64))
        return int(payload.get("exp", 0))
    except Exception:
        return 0

def _token_still_valid(token: Optional[str], min_ttl: int = MIN_TTL_BUFFER) -> bool:
    if not token:
        return False
    now = int(time.time())
    return _jwt_exp(token) > (now + min_ttl + CLOCK_SKEW)


def _collect_token() -> str:
    # First, checks if the already existing token is still valid
    existing = os.environ.get("LICENSETOKEN")
    if _token_still_valid(existing):
        return existing
    
    # If the token is not valid, fetchs for a new one
    activation_id = get_secret("EAISYDOCSLICENSE")  # contains activationId
    try:
        resp = requests.post(TOKEN_URL, json={"activationId": activation_id}, timeout=10)
        resp.raise_for_status()
        token = resp.json().get("token")
        if not token:
            # If server replied but no token, fall back to existing if it hasn't expired yet
            return existing if _token_still_valid(existing, min_ttl=0) else None
        os.environ["LICENSETOKEN"] = token
        return token
    except requests.RequestException:
        # Network/server issue: keep using existing token if it’s still time-valid
        return existing if _token_still_valid(existing, min_ttl=0) else None
    
def _verify_license(action: str) -> Dict[str, Any]:
    """Return decoded claims if the current token is valid; otherwise raise."""
    # Checks for valid license and tokens
    token: Optional[str] = _collect_token()
    if not token:
        raise LicenseError("Could not validate your license")

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise LicenseError("Missing value in token header")
    
    # Decodes the token to collect plan and permissions
    pem = _get_key_for_kid(kid)
    claims = jwt.decode(
        token,
        pem,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={"verify_aud": False, "leeway": 5},
    )
    features = json.loads(claims.get("feat"))

    # Start making validations
    if action == "CREATE-TOPIC":
        count_topics = len(topics.list_topics())
        max_topics = int(features.get("topics"))
        if count_topics >= max_topics:
            raise LimitsError("You have reached your plan maximum for this action")
        
    elif action == "QUERY":
        # TODO: Count daily queries
        pass


class LicenseError(Exception):
    pass

class LimitsError(Exception):
    pass

def require_license_api(
    *,
    action: Optional[str] = None
):
    
    def decorator(func: Callable) -> Callable:
        """FastAPI-friendly decorator: raises HTTP 403 on invalid license/token.
        Injects claims as kwarg `license_claims`."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                _verify_license(action)
            except (LimitsError, LicenseError, Exception) as e:
                 return JSONResponse({"status": "error", "message": f"{e}"}, status_code=400)
            return await func(*args, **kwargs)
        return wrapper
    return decorator