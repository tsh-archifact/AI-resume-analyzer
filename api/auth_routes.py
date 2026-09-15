from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth import TokenResponse, UserCreate, UserResponse
from services.auth_service import authenticate_user, create_access_token, create_user, get_current_user


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate):
    return create_user(user.username, user.password)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(user)
    return TokenResponse(access_token=access_token, expires_in=expires_in, user=user)


@router.get("/me", response_model=UserResponse)
def current_user(current_user: dict = Depends(get_current_user)):
    return current_user