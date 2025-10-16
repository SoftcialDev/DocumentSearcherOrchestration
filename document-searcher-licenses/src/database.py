import asyncpg
from config import settings

_pool: asyncpg.pool.Pool | None = None

async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(dsn=settings.PG_DSN, min_size=1, max_size=5)

async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def pool():
    return _pool

async def fetchrow(q, *args):
    conn = await _pool.acquire()
    try:
        return await conn.fetchrow(q, *args)
    finally:
        await _pool.release(conn)

async def execute(q, *args):
    conn = await _pool.acquire()
    try:
        return await conn.execute(q, *args)
    finally:
        await _pool.release(conn)
