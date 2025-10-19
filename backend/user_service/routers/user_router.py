from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.db.database import get_db
from backend.models.user_models import User

router = APIRouter(
    prefix="/user",
    tags=["Users"]
)
@router.get("/get_user/{user_id}")
async def get_user(username: str, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.email == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id, "email": user.email}