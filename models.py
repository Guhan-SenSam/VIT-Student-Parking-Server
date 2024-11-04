from enum import Enum
from sqlalchemy import Column, ForeignKey, Integer, DateTime, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base
from fastapi_users import schemas
from fastapi_users.db import SQLAlchemyBaseUserTable
from pydantic import EmailStr

class VehicleType(Enum):
    two_wheeler = "two_wheeler"
    four_wheeler = "four_wheeler"

class ActionType(Enum):
    entry = "entry"
    exit = "exit"
    
class User(SQLAlchemyBaseUserTable, Base):
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
# User Pydantic model
class UserCreate(schemas.BaseUserCreate):
    email: EmailStr

class UserUpdate(schemas.BaseUserUpdate):
    pass

class UserDB(schemas.BaseUser):
    pass


class ParkingLots(Base):
    __tablename__ = "parking_lots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    two_wheeler_capacity = Column(Integer)
    four_wheeler_capacity = Column(Integer)
    
    vehicle_logs = relationship("VehicleLog", back_populates="lot")
    

class VehicleLog(Base):
    __tablename__ = "vehicle_log"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lot_id = Column(Integer, ForeignKey("parking_lots.id"), index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    vehicle_type = Column(String, nullable=False)
    action = Column(String, nullable=False)
    
    lot = relationship("ParkingLots", back_populates="vehicle_logs")
