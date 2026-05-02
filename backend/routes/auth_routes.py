"""
auth_routes.py - Signup and Login API Endpoints

POST /api/signup  - Register a new user
POST /api/login   - Login and get a JWT token
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api", tags=["Authentication"])


# ---- Request body schemas (what the frontend sends) ----

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str


# ---- Endpoints ----

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    existing_name = db.query(User).filter(User.username == req.username).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create new user with hashed password
    new_user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return a token so they're logged in immediately after signup
    token = create_access_token({"user_id": new_user.id, "username": new_user.username})
    return {"token": token, "username": new_user.username}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id, "username": user.username})
    return {"token": token, "username": user.username}
