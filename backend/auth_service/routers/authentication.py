

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import Session
from backend.db.database import get_db
from sqlmodel import select
from backend.models.user_models import User

from .. import schemas, hashing, jwt_token

router = APIRouter(
    tags=["Authentication"] 
)

@router.post("/login/", response_model=schemas.Token)
async def login_for_access_token( 
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db:Session=Depends(get_db)
):

    
  
    db_user = db.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not db_user or not hashing.verify_password(form_data.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
          
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = jwt_token.create_access_token(
        data={"sub": str(db_user.id)}
    )
    
    return schemas.Token(access_token=access_token, token_type="bearer")
