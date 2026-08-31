from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.common import MessageResponse
from app.models.user import User, UserStatus
from app.services.auth_service import verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user via email & password.
    Returns JWT access token and sets secure HTTP-only cookie.
    """
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended."
        )

    # Generate JWT
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.value
    }
    access_token = create_access_token(data=token_data)

    # Set secure cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24, # 24 hours
        samesite="lax",
        secure=False # Set to True in production HTTPS
    )

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        teacher_id=user.teacher_profile.id if user.teacher_profile else None,
        employee_number=user.teacher_profile.employee_number if user.teacher_profile else None
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp
    )

@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logs out user by clearing the authentication cookie."""
    response.delete_cookie("access_token")
    return MessageResponse(message="Successfully logged out.")

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        status=current_user.status,
        teacher_id=current_user.teacher_profile.id if current_user.teacher_profile else None,
        employee_number=current_user.teacher_profile.employee_number if current_user.teacher_profile else None
    )
