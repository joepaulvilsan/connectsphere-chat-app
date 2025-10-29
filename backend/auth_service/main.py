from fastapi import FastAPI
from backend.auth_service.routers import authentication, users
from backend.db.database import create_db_and_tables

app = FastAPI(
    title="ConnectSphere Auth Service (In-Memory)",
    description="Handles user registration and login without a real database for Week 2."
)

@app.on_event("startup")
async def on_startup():
    """Initialize database tables on application startup."""
    create_db_and_tables()

app.include_router(authentication.router)
app.include_router(users.router)

@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to check if the service is running."""
    return {"message": "Welcome to the ConnectSphere in-memory Auth Service!"}
