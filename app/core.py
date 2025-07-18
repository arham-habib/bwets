import os, jwt
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_JWT_SECRET = "supabase"  # Supabase always signs with 'supabase' unless rotated

engine  = create_async_engine(DATABASE_URL, echo=False, future=True)
Session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with Session() as s:
        yield s

# ---- Auth helper ----
def require_user(req: Request):
    hdr = req.headers.get("authorization")
    if not hdr or not hdr.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing JWT")
    try:
        token = hdr.split()[1]
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        email = payload["email"]
        if not email.endswith("@bwater.com"):
            raise HTTPException(status_code=403, detail="domain not allowed")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid token")
