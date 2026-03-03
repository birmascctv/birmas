from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import User
from backend.schemas import UserCreate, UserLogin, UserOut
import bcrypt
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

    # bcrypt requires bytes, truncate if longer than 72
    raw_pw = user.password.encode("utf-8")[:72]
    hashed_pw = bcrypt.hashpw(raw_pw, bcrypt.gensalt()).decode("utf-8")

    new_user = User(username=user.username, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user registered: {user.username} (id={new_user.id})")
    return new_user

@router.post("/login", response_model=UserOut)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        logger.warning(f"Failed login attempt for {user.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    raw_pw = user.password.encode("utf-8")[:72]
    if not bcrypt.checkpw(raw_pw, db_user.password_hash.encode("utf-8")):
        logger.warning(f"Failed login attempt for {user.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    logger.info(f"User {user.username} logged in successfully (id={db_user.id})")
    return db_user
