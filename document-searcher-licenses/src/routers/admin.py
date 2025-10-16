from fastapi import APIRouter
from schemas import IssueIn, IssueOut
from database import execute
from uuid import uuid4
import os, json

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/issue")
async def issue(body: IssueIn):
    lic_id = uuid4()
    features_json = json.dumps({"topics": 5, "dailyQueries": 5}) # This should be built from body.plan
    SCHEME = os.getenv("SCHEME")

    await execute(f"""
      INSERT INTO {SCHEME}.licenses(id, product, plan, owner_email, seats, allowed_features, status, valid_from, valid_to)
      VALUES($1,'docsearch',$2,$3,$4,$5,'active',$6,$7)
      ON CONFLICT (id) DO UPDATE SET
        plan=EXCLUDED.plan, owner_email=EXCLUDED.owner_email, seats=EXCLUDED.seats,
        valid_from=EXCLUDED.valid_from, valid_to=EXCLUDED.valid_to, status='active', updated_at=now()
    """, str(lic_id), body.plan, body.ownerEmail, body.seats, features_json, body.validFrom, body.validTo)
    return IssueOut(id=lic_id, ok=True)
