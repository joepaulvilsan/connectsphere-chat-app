from fastapi import FastAPI
from .routers import user_router
from backend.db.database import create_db_and_tables

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Initialize database tables on application startup."""
    create_db_and_tables()

app.include_router(user_router.router)

