from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import APIKey, KeyStatus
import uuid
from datetime import datetime
from sqlalchemy import text


app = FastAPI()

@app.post("/keys/create")
async def create_key(parent_id: str = None, db: AsyncSession = Depends(get_db)):
    # If parent_id is provided, check if it exists
    parent = None
    if parent_id:
        result = await db.execute(select(APIKey).where(APIKey.id == parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent key not found")

    # Create new key
    new_key = APIKey(
        id=str(uuid.uuid4()),
        key=str(uuid.uuid4()),
        parent_id=parent_id,
        status=KeyStatus.active,
        created_at=datetime.utcnow()
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return {
        "id": new_key.id,
        "key": new_key.key,
        "parent_id": new_key.parent_id,
        "status": new_key.status
    }
@app.get("/keys/validate/{key}")
async def validate_key(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(APIKey).where(APIKey.key == key, APIKey.status == KeyStatus.active)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Key not found or revoked")
    return {"message": "Key is valid", "id": api_key.id}

# Helper function to recursively revoke all descendants
async def revoke_descendants(parent_id: str, db: AsyncSession):
    result = await db.execute(select(APIKey).where(APIKey.parent_id == parent_id))
    children = result.scalars().all()

    for child in children:
        child.status = KeyStatus.revoked
        child.revoked_at = datetime.utcnow()
        await revoke_descendants(child.id, db)

# Endpoint to revoke key and all its descendants
@app.post("/keys/revoke/{key_id}")
async def revoke_key(key_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    key.status = KeyStatus.revoked
    key.revoked_at = datetime.utcnow()

    # Recursively revoke all children
    await revoke_descendants(key_id, db)

    await db.commit()
    return {"message": f"Key {key_id} and all descendant keys revoked"}