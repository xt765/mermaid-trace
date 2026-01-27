"""
SQLAlchemy, FastAPI, and Pydantic Integration.
Demonstrates:
1. Tracing database operations with SQLAlchemy
2. Validating data with Pydantic and tracing the process
3. FastAPI middleware orchestration
4. Manual participant naming for architectural clarity
"""

import os
from typing import List, Generator, Any
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from mermaid_trace import trace, configure_flow, trace_class, patch_object
from mermaid_trace.integrations.fastapi import MermaidTraceMiddleware
import uvicorn

# 1. Setup tracing - Using a dedicated file for this complex example
output_dir = "mermaid_diagrams/examples"
os.makedirs(output_dir, exist_ok=True)
configure_flow(os.path.join(output_dir, "full_stack_app.mmd"))

# 2. Database Setup
Base: Any = declarative_base()
engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class UserDB(Base):  # type: ignore
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)


Base.metadata.create_all(bind=engine)


# 3. Pydantic Models with tracing
@trace_class(name="Schema")
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: str


@trace_class(name="Schema")
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


# 4. Service Layer with explicit naming
@trace_class(name="UserService")
class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_in: UserCreate) -> UserDB:
        db_user = UserDB(username=user_in.username, email=user_in.email)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_users(self) -> List[UserDB]:
        return list(self.db.execute(select(UserDB)).scalars().all())


# 5. Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 6. FastAPI App
app = FastAPI(title="Full Stack Tracing Demo")

# Add middleware for automatic request tracing
app.add_middleware(MermaidTraceMiddleware, app_name="WebPortal")


@app.post("/users/", response_model=UserResponse)
@trace(name="WebPortal", action="Create User Endpoint")
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserDB:
    service = UserService(db)
    # Check if exists
    existing = db.execute(
        select(UserDB).where(UserDB.username == user.username)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    return service.create_user(user)


@app.get("/users/", response_model=List[UserResponse])
@trace(name="WebPortal", action="List Users Endpoint")
async def list_users(db: Session = Depends(get_db)) -> List[UserDB]:
    service = UserService(db)
    return service.get_users()


# 7. Patching SQLAlchemy for internal visibility (Optional but powerful)
# We can patch specific Session methods to see them in the diagram
patch_object(Session, "add", name="Database", action="SQL: INSERT")
patch_object(Session, "commit", name="Database", action="SQL: COMMIT")
patch_object(Session, "execute", name="Database", action="SQL: SELECT/QUERY")

if __name__ == "__main__":
    print("Starting Full Stack Demo on http://127.0.0.1:8002")
    print(
        '1. Create a user: curl -X POST http://127.0.0.1:8002/users/ -H \'Content-Type: application/json\' -d \'{"username": "alice", "email": "alice@example.com"}\''
    )
    print("2. List users: curl http://127.0.0.1:8002/users/")
    print("Check mermaid_diagrams/examples/full_stack_app.mmd for the trace!")

    uvicorn.run(app, host="127.0.0.1", port=8002)
