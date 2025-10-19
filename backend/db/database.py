from sqlmodel import SQLModel, create_engine

DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5433/connectsphere_db"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db():
    db=Session(engine)
    try:
        yield db
    finally:
        db.close()  