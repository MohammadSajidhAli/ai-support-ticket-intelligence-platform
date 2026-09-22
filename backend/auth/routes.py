from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.database import get_db
from models.user import UserDB
from auth.security import hash_password, verify_password, create_access_token
from auth.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


# ============================================================
# REGISTER
# ============================================================

@router.post("/register", response_model=UserResponse)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    # Publicly registered users are always viewers.
    # Admin and support_agent accounts should be provisioned
    # separately rather than selected during public registration.
    role = "viewer"

    # --------------------------------------------------------
    # PASSWORD VALIDATION
    # --------------------------------------------------------

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    # --------------------------------------------------------
    # USERNAME CHECK
    # --------------------------------------------------------

    existing_username = (
        db.query(UserDB)
        .filter(UserDB.username == request.username)
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    # --------------------------------------------------------
    # EMAIL CHECK
    # --------------------------------------------------------

    existing_email = (
        db.query(UserDB)
        .filter(UserDB.email == request.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    user = UserDB(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        role=role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(UserDB)
        .filter(UserDB.username == form_data.username)
        .first()
    )

    if user is None or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get("/me", response_model=UserResponse)
def me(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    return current_user
