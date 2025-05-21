from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid, secrets, enum

Base = declarative_base()

class KeyStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"

def generate_secure_key(length=32):
    return secrets.token_urlsafe(length)

class APIKey(Base):
    __tablename__ = 'api_keys'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, nullable=False, default=generate_secure_key)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('api_keys.id'), nullable=True)
    status = Column(Enum(KeyStatus), nullable=False, default=KeyStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    services = Column(ARRAY(String), default=[])

    parent = relationship('APIKey', remote_side=[id], backref='children')
