from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from PROVIDER.models import APIKey, KeyStatus
from PROVIDER.database import get_db
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI(docs_url="/docs", redoc_url="/redoc")

ALLOWED_SERVICES = {"A", "B", "C", "D", "E"}

@app.post("/keys/create")
async def create_key(
    parent_id: Optional[str] = None,
    services: Optional[List[str]] = None,
    expires_in_days: Optional[int] = 7,  # ⬅️ Default to 7-day license
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

    expires_at = datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None

    new_key = APIKey(
        id=str(uuid.uuid4()),
        key=str(uuid.uuid4()),
        parent_id=parent_id,
        status=KeyStatus.active,
        created_at=datetime.utcnow(),
        services=services if services else list(parent_services),
        expires_at=expires_at  # ⬅️ Add here
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return {
        "id": new_key.id,
        "key": new_key.key,
        "parent_id": new_key.parent_id,
        "status": new_key.status,
        "services": new_key.services,
        "expires_at": new_key.expires_at.isoformat() if new_key.expires_at else None
    }


@app.get("/keys/validate/{key}")
async def validate_key(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(APIKey).where(APIKey.key == key, APIKey.status == KeyStatus.active))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Key not found or revoked")

    # ⬇️ Check expiration
    if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
        raise HTTPException(status_code=403, detail="Key expired")

    return {
        "message": "Key is valid",
        "id": api_key.id,
        "services": api_key.services,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None
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


import sys, os
from fastapi import HTTPException
from pydantic import BaseModel

# Make sure these are at the top of your file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "MOHPART")))

from encryptor import encrypt_file
from client import (
    load_state,
    validate_api_key,
    update_last_online,
    check_offline_duration,
    GRACE_PERIOD_DAYS,
    FUNCTIONAL,
    EXPIRED_GRACE,
    ENCRYPTED_EXPIRED,
    ENCRYPTED_OFFLINE,
    save_state
)

class EncryptRequest(BaseModel):
    filename: str
    api_key: str

@app.post("/encrypt_file")
def encrypt_request(req: EncryptRequest):
    state = load_state()
    valid, status = validate_api_key(req.api_key)

    if status == "VALID":
        update_last_online(state)
        state["status"] = FUNCTIONAL

    elif status == "EXPIRED":
        if check_offline_duration(state.get("last_online")) <= GRACE_PERIOD_DAYS:
            state["status"] = EXPIRED_GRACE
        else:
            state["status"] = ENCRYPTED_EXPIRED
            save_state(state)
            raise HTTPException(status_code=403, detail="Key expired and grace period exceeded.")

    elif status == "OFFLINE":
        if check_offline_duration(state.get("last_online")) > GRACE_PERIOD_DAYS:
            state["status"] = ENCRYPTED_OFFLINE
            save_state(state)
            raise HTTPException(status_code=403, detail="Offline too long. Encryption disabled.")

    else:
        state["status"] = ENCRYPTED_EXPIRED
        save_state(state)
        raise HTTPException(status_code=403, detail="Invalid key.")

    # ✅ Save the updated state after all logic passes
    save_state(state)

    # ✅ Make sure the input file exists
    if not os.path.exists(req.filename):
        raise HTTPException(status_code=404, detail="File not found.")

    # ✅ Encrypt the file
    output_path = req.filename + ".enc"
    encrypt_file(req.filename, output_path, req.api_key)

    return {"status": "success", "output_file": output_path}
