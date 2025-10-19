from fastapi import FastAPI
from routers import authentication, users

app = FastAPI(
    title="ConnectSphere Auth Service (In-Memory)",
    description="Handles user registration and login without a real database for Week 2."
)

app.state.fake_user_db = []
app.state.user_id_counter = 0

app.include_router(authentication.router)
app.include_router(users.router)

@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to check if the service is running."""
    return {"message": "Welcome to the ConnectSphere in-memory Auth Service!"}
