from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

app = FastAPI()

@app.get("/")
async def root(db: AsyncSession = Depends(get_db)):#create safe and fresh database session(automatic close)
    return {"message": "Connected to database successfully!"}
