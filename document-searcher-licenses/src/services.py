from datetime import datetime, timedelta, timezone
import uuid
from database import fetchrow, execute
from config import settings
from crypto import make_claims, build_jwt

async def get_license(license_id):
    return await fetchrow("""
      SELECT id, plan, seats, status, valid_from, valid_to, allowed_features
      FROM licenses.licenses WHERE id=$1
    """, license_id)

async def seats_in_use(license_id):
    return await fetchrow("""
      SELECT count(*) AS c FROM licenses.activations
      WHERE license_id=$1
        AND status='active'
        AND last_heartbeat > now() - interval '2 hours'
    """, license_id)

async def create_activation(license_id, version):
    act_id = uuid.uuid4()
    await execute("""
      INSERT INTO licenses.activations(id, license_id, hw_id, client_version, status)
      VALUES($1,$2,$3,$4,'active')
    """, act_id, license_id, "hw_id", version)
    return act_id

async def touch_activation(act_id):
    # ensure it exists & matches device
    row = await fetchrow("SELECT license_id FROM licenses.activations WHERE id=$1", act_id)
    if not row:
        return None
    await execute("UPDATE licenses.activations SET last_heartbeat=now() WHERE id=$1", act_id)
    return row["license_id"]

def token_from(license_row, activation_id):
    claims = make_claims(license_row, activation_id, settings.TOKEN_TTL_MIN)
    token = build_jwt(claims)
    return token, claims["exp"]

async def is_license_active_now(lic):
    now = datetime.now(timezone.utc)
    return (lic["status"] == "active" and lic["valid_from"] <= now <= lic["valid_to"])
