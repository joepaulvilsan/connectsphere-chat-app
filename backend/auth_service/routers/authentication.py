

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

import schemas, hashing, jwt_token

router = APIRouter(
    tags=["Authentication"] 
)

@router.post("/login/", response_model=schemas.Token)
async def login_for_access_token(
    request: Request, 
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):

    fake_user_db = request.app.state.fake_user_db
    
  
    db_user = None
    for user in fake_user_db:
        if user["email"] == form_data.username:
            db_user = user
            break

    if not db_user or not hashing.verify_password(form_data.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
          
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = jwt_token.create_access_token(
        data={"sub": str(db_user["id"])}
    )
    
    return schemas.Token(access_token=access_token, token_type="bearer")
