import base64, json, uuid, hashlib
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm
from config import settings


_cred = DefaultAzureCredential()
_key_client = KeyClient(vault_url=settings.KV_URL, credential=_cred)
_key = _key_client.get_key(settings.KEY_NAME)             # has public parts (n,e)
_signer = CryptographyClient(_key.id, credential=_cred)   # signs with private key

def _b64url(b: bytes) -> bytes:
    return base64.urlsafe_b64encode(b).rstrip(b"=")

def build_jwt(claims: dict) -> str:
    header = {"alg": "RS256", "typ": "JWT", "kid": _key.properties.name}
    enc_header = _b64url(json.dumps(header, separators=(",",":")).encode())
    enc_payload = _b64url(json.dumps(claims, separators=(",",":")).encode())
    signing_input = enc_header + b"." + enc_payload
    sig = _signer.sign(SignatureAlgorithm.rs256,  hashlib.sha256(signing_input).digest()).signature
    enc_sig = _b64url(sig)
    return (signing_input + b"." + enc_sig).decode()

def make_claims(license_row, activation_id, ttl_min: int):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ttl_min)
    return {
        "iss": settings.ISSUER,
        "sub": str(license_row["id"]),
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "plan": license_row["plan"],
        "seats": license_row["seats"],
        "feat" : license_row["allowed_features"],
        "act": str(activation_id),
    }

def jwk_set() -> dict:
    # Convert RSA public key to JWK (n and e are base64url without padding)
    n = _key.key.n  # bytes
    e = _key.key.e  # bytes
    return {
        "keys": [{
            "kty": "RSA",
            "kid": _key.properties.name,
            "use": "sig",
            "alg": "RS256",
            "n": _b64url(n).decode(),
            "e": _b64url(e).decode(),
        }]
    }
