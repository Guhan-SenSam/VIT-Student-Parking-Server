from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import ParkingLots
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from database import engine
from models import Base 

# load environment variables
load_dotenv()

app = FastAPI()
SECRET_KEY = os.getenv("DEVICE_SECRET_KEY", "this is a test key")

# Create all tables
Base.metadata.create_all(bind=engine)

class DeviceData(BaseModel):
    device_key: str
    lot_id: int
    two_wheeler_count: int
    four_wheeler_count: int

@app.post("/iot/parking_data")
async def receive_data(data: DeviceData, db: Session = Depends(get_db)):
    if data.device_key != SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid device key")
    # # parking_entry = ParkingData(
    # #     lot_id=data.lot_id,
    # #     two_wheeler_count=data.two_wheeler_count,
    # #     four_wheeler_count=data.four_wheeler_count
    # # )
    # db.add(parking_entry)
    # db.commit()
    # db.refresh(parking_entry)
    # return {"message": "Data received", "entry_id": parking_entry.id}

@app.get("/iot/client_data")
async def get_client_data(db: Session = Depends(get_db)):
    data = db.query(ParkingLots).all()
    return data
