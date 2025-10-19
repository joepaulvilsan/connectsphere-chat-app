from fastapi import FastAPI
from .routers import user_router
from backend.db.database import create_db_and_tables
create_db_and_tables()
app = FastAPI()

app.include_router(user_router.router)


