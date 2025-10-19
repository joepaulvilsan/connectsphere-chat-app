import typing
from fastapi import APIRouter, status, Request
import schemas, hashing
from backend.models.user_models import User
from backend.db.database import get_db
from sqlmodel import Session, select
from fastapi import Depends, HTTPException

router = APIRouter(
    prefix="/user", 
    tags=["Users"]  
)

@router.post("/register/", response_model=schemas.UserDisplay, status_code=status.HTTP_201_CREATED)
async def create_user(user:schemas.UserCreate,db:Session=Depends(get_db)):
    existing_user = db.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = hashing.Hash.bcrypt(user.password)
    new_user = User(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user