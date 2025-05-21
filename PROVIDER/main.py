from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import APIKey, KeyStatus
from database import get_db
import uuid
from datetime import datetime

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

ALLOWED_SERVICES = {"A", "B", "C", "D", "E"}

@app.post("/keys/create")
async def create_key(
    parent_id: Optional[str] = None,
    services: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    parent_services = set(ALLOWED_SERVICES)

    if parent_id:
        result = await db.execute(select(APIKey).where(APIKey.id == parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent key not found")
        parent_services = set(parent.services)

    if services:
        invalid = set(services) - parent_services
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid service(s): {', '.join(invalid)}. Allowed: {', '.join(parent_services)}"
            )

    new_key = APIKey(
        id=str(uuid.uuid4()),
        key=str(uuid.uuid4()),
        parent_id=parent_id,
        status=KeyStatus.active,
        created_at=datetime.utcnow(),
        services=services if services else list(parent_services)
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return {
        "id": new_key.id,
        "key": new_key.key,
        "parent_id": new_key.parent_id,
        "status": new_key.status,
        "services": new_key.services
    }

@app.get("/keys/validate/{key}")
async def validate_key(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.key == key, APIKey.status == KeyStatus.active))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Key not found or revoked")
    return {
        "message": "Key is valid",
        "id": api_key.id,
        "services": api_key.services  # ✅ Add this line
    }

@app.post("/keys/revoke/{key_id}")
async def revoke_key(key_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    key.status = KeyStatus.revoked
    key.revoked_at = datetime.utcnow()
    await revoke_descendants(key_id, db)
    await db.commit()
    return {"message": f"Key {key_id} and descendants revoked"}

async def revoke_descendants(parent_id: str, db: AsyncSession):
    result = await db.execute(select(APIKey).where(APIKey.parent_id == parent_id))
    children = result.scalars().all()
    for child in children:
        child.status = KeyStatus.revoked
        child.revoked_at = datetime.utcnow()
        await revoke_descendants(child.id, db)

@app.post("/keys/activate/{key_id}")
async def activate_key(key_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    key.status = KeyStatus.active
    key.revoked_at = None
    await activate_descendants(key.id, db)
    await db.commit()
    return {"message": f"Key {key_id} and descendants activated"}

async def activate_descendants(parent_id: str, db: AsyncSession):
    result = await db.execute(select(APIKey).where(APIKey.parent_id == parent_id))
    children = result.scalars().all()
    for child in children:
        child.status = KeyStatus.active
        child.revoked_at = None
        await activate_descendants(child.id, db)