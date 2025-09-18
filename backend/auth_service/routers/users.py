from fastapi import APIRouter, status, Request
import schemas, hashing

router = APIRouter(
    prefix="/user", 
    tags=["Users"]  
)

@router.post("/register/", response_model=schemas.UserDisplay, status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, request: Request):

    fake_user_db = request.app.state.fake_user_db
    user_id_counter = request.app.state.user_id_counter

    hashed_password = hashing.hash_password(user.password)

    user_id_counter += 1
    request.app.state.user_id_counter = user_id_counter

    new_user = {
        "id": user_id_counter,
        "email": user.email,
        "password_hash": hashed_password
    }

    fake_user_db.append(new_user)
    
    return new_user


