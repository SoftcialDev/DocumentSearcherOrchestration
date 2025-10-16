from fastapi import APIRouter, HTTPException
from schemas import ActivateIn, ActivateOut, HeartbeatIn, HeartbeatOut
from services import *
from crypto import jwk_set
from config import settings

router = APIRouter(prefix="/client", tags=["client"])

@router.post("/activate", response_model=ActivateOut)
async def activate(body: ActivateIn):
    lic = await get_license(str(body.licenseId))
    if not lic or not await is_license_active_now(lic):
        raise HTTPException(403, f"License not active")
    used = (await seats_in_use(lic["id"]))["c"]
    if used >= lic["seats"]:
        raise HTTPException(429, "No seats available")
    act_id = await create_activation(lic["id"], body.clientVersion)
    token, exp = token_from(lic, act_id)
    return ActivateOut(activationId=act_id, token=token, expiresAt=exp)

@router.post("/heartbeat", response_model=HeartbeatOut)
async def heartbeat(body: HeartbeatIn):
    lic_id = await touch_activation(body.activationId)
    if not lic_id:
        raise HTTPException(403, "Activation not found")

    lic = await get_license(str(lic_id))
    if not lic or not await is_license_active_now(lic):
        raise HTTPException(403, "License not active")

    token, exp = token_from(lic, body.activationId)
    return HeartbeatOut(token=token, expiresAt=exp)

@router.get("/pubkey")
async def pubkey():
    return jwk_set()
