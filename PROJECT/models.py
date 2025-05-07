from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import enum
import uuid
from datetime import datetime

Base = declarative_base()

class KeyStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"

class APIKey(Base):
    __tablename__ = 'api_keys'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    parent_id = Column(UUID(as_uuid=True), ForeignKey('api_keys.id'), nullable=True)
    status = Column(Enum(KeyStatus), nullable=False, default=KeyStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    parent = relationship('APIKey', remote_side=[id], backref='children')
