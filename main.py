from datetime import date, timedelta
import datetime
from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import ActionType, ParkingLots, VehicleLog, VehicleType
from sqlalchemy import func
from pydantic import BaseModel,EmailStr
import os
from dotenv import load_dotenv
from database import engine
from models import Base
from smtp import send_verification_email
import jwt

# load environment variables
load_dotenv()
# print all environment variables
print(os.environ)

app = FastAPI()
SECRET_KEY = os.getenv("DEVICE_SECRET_KEY", "shfodsfsd235nsY8")

# Create all tables
Base.metadata.create_all(bind=engine)

# Predefined parking lot data
parking_lots_data = [
    {"name": "Student parking 1", "two_wheeler_capacity": 50, "four_wheeler_capacity": 30},
    {"name": "Mg Auditorium", "two_wheeler_capacity": 100, "four_wheeler_capacity": 60},
    {"name": "Externak Parking", "two_wheeler_capacity": 70, "four_wheeler_capacity": 50},
]

# Function to preload parking lots
def preload_parking_lots(db: Session):
    for lot in parking_lots_data:
        existing_lot = db.query(ParkingLots).filter(ParkingLots.name == lot["name"]).first()
        if not existing_lot:
            new_lot = ParkingLots(**lot)
            db.add(new_lot)
    db.commit()

# FastAPI event to run on startup
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        preload_parking_lots(db)
    finally:
        db.close()


# Endpoint to request a token via email
@app.post("/auth/request-token")
async def request_token(email: EmailStr):
    # Check if the email belongs to the institute
    if not email.endswith("@vitstudent.ac.in"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email domain. Only @vitstudent.ac.in emails are allowed."
        )

    # Generate a token (valid for 15 minutes)
    expiration = datetime.datetime.utcnow() + timedelta(minutes=15)
    token = jwt.encode({"sub": email, "exp": expiration}, SECRET_KEY, algorithm="HS256")

    # Send the token to the user's email
    await send_verification_email(email, token)
    return {"msg": "Verification email sent"}

# Endpoint to verify the token
@app.post("/auth/verify-token")
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        return {"msg": "Token verified", "email": email}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

# Middleware to handle authentication
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication")

class DeviceData(BaseModel):
    device_key: str
    lot_id: int
    vehicle_type: VehicleType
    action: ActionType
    
@app.get("/api/parking_lots")
async def get_parking_lots(db: Session = Depends(get_db)):
    lots = db.query(ParkingLots).all()
    return lots

@app.post("/api/new_log")
async def receive_data(data: DeviceData, db: Session = Depends(get_db)):
    if data.device_key != SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid device key")

    lot = db.query(ParkingLots).filter(ParkingLots.id == data.lot_id).first()
    if not lot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking lot not found")
    new_log = VehicleLog(
        lot_id=data.lot_id,
        vehicle_type=data.vehicle_type.value,
        action=data.action.value
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return {"message": "Data recorded", "log_id": new_log.id}

@app.get("/iot/vehicle_logs")
def get_vehicle_logs(
    lot_id: int,
    start_date: date = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: date = Query(None, description="End date in YYYY-MM-DD format"),
    today: bool = Query(False, description="Set to true to get today's logs only"),
    db: Session = Depends(get_db)
):
    lot = db.query(ParkingLots).filter(ParkingLots.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    query = db.query(VehicleLog).filter(VehicleLog.lot_id == lot_id)
    
    if today:
        start_of_today = datetime.combine(date.today(), datetime.min.time())
        end_of_today = datetime.combine(date.today(), datetime.max.time())
        query = query.filter(VehicleLog.timestamp.between(start_of_today, end_of_today))
    else:
        # Filter by date range
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(VehicleLog.timestamp >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(VehicleLog.timestamp <= end_datetime)

    logs = query.order_by(VehicleLog.timestamp).all()
    return logs

@app.get("/iot/lot_summary")
def get_lot_summary(db: Session = Depends(get_db)):
    summary = []
    lots = db.query(ParkingLots).all()

    for lot in lots:
        two_wheeler_count = db.query(func.count(VehicleLog.id)).filter(
            VehicleLog.lot_id == lot.id,
            VehicleLog.vehicle_type == VehicleType.two_wheeler.value,
            VehicleLog.action == ActionType.entry.value
        ).scalar() - db.query(func.count(VehicleLog.id)).filter(
            VehicleLog.lot_id == lot.id,
            VehicleLog.vehicle_type == VehicleType.two_wheeler.value,
            VehicleLog.action == ActionType.exit.value
        ).scalar()

        four_wheeler_count = db.query(func.count(VehicleLog.id)).filter(
            VehicleLog.lot_id == lot.id,
            VehicleLog.vehicle_type == VehicleType.four_wheeler.value,
            VehicleLog.action == ActionType.entry.value
        ).scalar() - db.query(func.count(VehicleLog.id)).filter(
            VehicleLog.lot_id == lot.id,
            VehicleLog.vehicle_type == VehicleType.four_wheeler.value,
            VehicleLog.action == ActionType.exit.value
        ).scalar()
        available_two_wheeler_spots = lot.two_wheeler_capacity - two_wheeler_count
        available_four_wheeler_spots = lot.four_wheeler_capacity - four_wheeler_count
        two_wheeler_percentage = (two_wheeler_count / lot.two_wheeler_capacity) * 100 if lot.two_wheeler_capacity > 0 else 0
        four_wheeler_percentage = (four_wheeler_count / lot.four_wheeler_capacity) * 100 if lot.four_wheeler_capacity > 0 else 0
        overall_percentage = ((two_wheeler_count + four_wheeler_count) / (lot.two_wheeler_capacity + lot.four_wheeler_capacity)) * 100 if (lot.two_wheeler_capacity + lot.four_wheeler_capacity) > 0 else 0

        summary.append({
            "lot_id": lot.id,
            "lot_name": lot.name,
            "current_two_wheeler_count": two_wheeler_count,
            "current_four_wheeler_count": four_wheeler_count,
            "available_two_wheeler_spots": available_two_wheeler_spots,
            "available_four_wheeler_spots": available_four_wheeler_spots,
            "two_wheeler_percentage_full": two_wheeler_percentage,
            "four_wheeler_percentage_full": four_wheeler_percentage,
            "overall_percentage_full": overall_percentage
        })

    return summary



