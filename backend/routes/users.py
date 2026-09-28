import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models import User
from backend.schemas import UserCreate, UserLogin, UserOut, TokenOut
from jose import jwt
import bcrypt
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn")
security = HTTPBearer()

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

@router.post("/login", response_model=TokenOut)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        logger.warning(f"Failed login attempt for {user.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    raw_pw = user.password.encode("utf-8")[:72]
    if not bcrypt.checkpw(raw_pw, db_user.password_hash.encode("utf-8")):
        logger.warning(f"Failed login attempt for {user.username}")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "B1rm4sC4m3r4")
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12"))
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": str(db_user.id),
        "username": db_user.username,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/verify")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    SECRET_KEY = os.getenv("SECRET_KEY", "B1rm4sC4m3r4")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"status": "ok", "user": payload.get("username")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
