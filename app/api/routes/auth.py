from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbDep
from app.core.security import create_token, decode_token
from app.schemas.auth import RefreshRequest, Token, UserCreate, UserRead
from app.services import users

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user_id: int) -> Token:
    sub = str(user_id)
    return Token(
        access_token=create_token(sub, "access"),
        refresh_token=create_token(sub, "refresh"),
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DbDep):
    if await users.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    return await users.create_user(db, data.email, data.password)


@router.post("/login", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbDep):
    # OAuth2 form uses "username" for the email field
    user = await users.authenticate(db, form.username, form.password)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return _issue_tokens(user.id)


@router.post("/refresh", response_model=Token)
async def refresh(data: RefreshRequest, db: DbDep):
    try:
        user_id = int(decode_token(data.refresh_token, "refresh"))
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = await users.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    return _issue_tokens(user.id)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser):
    return user
