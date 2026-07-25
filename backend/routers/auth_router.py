import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..db import get_db
from ..services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"          # "user" or "caregiver"
    substance_history: Optional[str] = None
    triggers: Optional[str] = None
    support_network: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    """
    Register a new user. Creates both a credentials row and a users profile row.
    """
    user_id = str(uuid.uuid4())
    hashed = hash_password(request.password)

    with get_db() as conn:
        # Check if email already exists
        existing = conn.execute(
            "SELECT id FROM credentials WHERE email = ?", [request.email]
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

        # Insert credentials
        conn.execute(
            """
            INSERT INTO credentials (id, email, hashed_password, role)
            VALUES (?, ?, ?, ?)
            """,
            [user_id, request.email, hashed, request.role]
        )

        # Insert user profile
        conn.execute(
            """
            INSERT INTO users (id, name, substance_history, triggers, support_network)
            VALUES (?, ?, ?, ?, ?)
            """,
            [user_id, request.name, request.substance_history,
             request.triggers, request.support_network]
        )

    return {"message": "Account created successfully.", "user_id": user_id}


@router.post("/login")
def login(request: LoginRequest):
    """
    Login with email and password. Returns a JWT Bearer token.
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, hashed_password, role, is_active FROM credentials WHERE email = ?",
            [request.email]
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user_id, hashed_password, role, is_active = row

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    if not verify_password(request.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token(data={"sub": user_id, "role": role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "role": role
    }
