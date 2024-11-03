from enum import Enum
from sqlalchemy import Column, ForeignKey, Integer, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class VehicleType(Enum):
    two_wheeler = "two_wheeler"
    four_wheeler = "four_wheeler"

class ActionType(Enum):
    entry = "entry"
    exit = "exit"


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
    
    lot = relationship("ParkingLot", back_populates="vehicle_logs")
