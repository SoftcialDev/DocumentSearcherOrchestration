from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from datetime import date, datetime, timezone

def _coerce_datetime(v):
    # Already a datetime/date?
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, date):
        # Convert date -> midnight UTC datetime
        return datetime(v.year, v.month, v.day, tzinfo=timezone.utc)

    if isinstance(v, str):
        s = v.strip()

        # Try ISO 8601 first (including trailing 'Z')
        try:
            iso = s[:-1] + "+00:00" if s.endswith("Z") else s
            dt = datetime.fromisoformat(iso)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

        # Try a few common non-ISO formats (add any you need)
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

    raise ValueError("Invalid date/datetime format")

class ActivateIn(BaseModel):
    licenseId: UUID
    clientVersion: str | None = None

class ActivateOut(BaseModel):
    activationId: UUID
    token: str
    expiresAt: int  # epoch seconds

class HeartbeatIn(BaseModel):
    activationId: UUID

class HeartbeatOut(BaseModel):
    token: str
    expiresAt: int

class IssueIn(BaseModel):
    ownerEmail: EmailStr
    plan: str = "pro"
    seats: int = 1
    validFrom: datetime
    validTo: datetime

    # v2-style validator; runs before type coercion
    @field_validator("validFrom", "validTo", mode="before")
    @classmethod
    def _parse_dates(cls, v):
        return _coerce_datetime(v)

class IssueOut(BaseModel):
    id: UUID
    ok: bool = True
