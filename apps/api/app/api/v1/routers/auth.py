"""Authentication router: register, login, profile."""

from fastapi import APIRouter, Depends
from app.core.deps import CurrentUser, get_current_user
from app.core.envelope import ApiResponse
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserProfile
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[TokenResponse])
async def register(req: UserCreate) -> ApiResponse[TokenResponse]:
    token = await auth_service.register(req)
    return ApiResponse.success(token)


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(req: UserLogin) -> ApiResponse[TokenResponse]:
    token = await auth_service.login(req)
    return ApiResponse.success(token)


@router.get("/me", response_model=ApiResponse[UserProfile])
async def get_current_user_profile(
    user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[UserProfile]:
    profile = await auth_service.get_profile(user.user_id)
    return ApiResponse.success(profile)
