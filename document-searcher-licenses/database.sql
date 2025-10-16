-- licenses: the product entitlement
CREATE TABLE IF NOT EXISTS licenses.licenses (
  id UUID PRIMARY KEY,
  product TEXT NOT NULL,                         -- are we having more that just eaisy docs?
  plan TEXT NOT NULL,                            -- "pro", "enterprise", etc.
  owner_email TEXT NOT NULL,                     -- client email for notifications
  seats INT NOT NULL DEFAULT 1,                  -- number of paying users, if required
  allowed_features JSONB NOT NULL,               -- ["rag","export","admin"]
  status TEXT NOT NULL,                          -- "active","revoked","suspended","expired"
  valid_from TIMESTAMPTZ NOT NULL,               -- starting subscription period
  valid_to   TIMESTAMPTZ NOT NULL,               -- ending subscription period
  node_locked BOOLEAN NOT NULL DEFAULT FALSE,    -- hardware fingerprint, probably not needed
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), -- first subscription date
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()  -- latest action on subscription date
);

-- activations: each device/session consuming a seat
CREATE TABLE IF NOT EXISTS licenses.activations (
  id UUID PRIMARY KEY,
  license_id UUID REFERENCES licenses(id) ON DELETE CASCADE,   -- foreign key for licenses
  hw_id TEXT,                                                  -- hash/fingerprint from client
  client_version TEXT,                                         -- version the user is currently using, if auto updates are disabled
  last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT now(),           -- last time the licenses was checked for validity
  status TEXT NOT NULL,                                        -- "active","released","revoked"
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()                -- when was the product activated
);

-- revocations: explicit invalidations at token-id (jti) or license scope
CREATE TABLE IF NOT EXISTS licenses.revocations (
  id UUID PRIMARY KEY,
  license_id UUID REFERENCES licenses(id) ON DELETE CASCADE,   -- foreign key for licenses
  jti TEXT,                                                    -- token id if revoking a specific token
  reason TEXT,                                                 -- why was the license revoked
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()                -- when was the license revoked
);

-- audit (optional)
CREATE TABLE IF NOT EXISTS licenses.audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor TEXT,                                    -- "system" or admin email
  action TEXT,                                   -- "ISSUE","REVOKE","HEARTBEAT","VALIDATE"
  subject_id TEXT,                               -- license or activation id
  meta JSONB,                                    -- extra data if needed
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()  -- when was the audit done
);
