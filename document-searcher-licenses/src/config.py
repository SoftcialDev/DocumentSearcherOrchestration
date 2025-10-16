import os

class Settings:
    PG_DSN = os.getenv("PG_DSN")
    KV_URL = os.getenv("KV_URL")
    KEY_NAME = os.getenv("KEY_NAME")
    ISSUER = os.getenv("ISSUER")
    TOKEN_TTL_MIN = int(os.getenv("TOKEN_TTL_MIN"))
    HEARTBEAT_GRACE_MIN = int(os.getenv("HEARTBEAT_GRACE_MIN"))

settings = Settings()
