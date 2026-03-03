from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import User
from backend.schemas import UserCreate, UserLogin, UserOut
from backend.auth import hash_password, verify_password
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(username=user.username, password_hash=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user registered: {user.username} (id={new_user.id})")
    return new_user

@router.post("/login", response_model=UserOut)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        logger.warning(f"Failed login attempt for {user.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    logger.info(f"User {user.username} logged in successfully (id={db_user.id})")
    return db_user
