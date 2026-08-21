"""Authentication service supporting JWT access token issuance and bcrypt password verification (FG-6, NFR-S1)."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from app.core.errors import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserProfile


class AuthService:
    def __init__(self):
        self.users: Dict[str, dict] = {}
        # Seed demo user
        demo_id = "user-demo-001"
        self.users["demo@tradly.ai"] = {
            "id": demo_id,
            "email": "demo@tradly.ai",
            "name": "Demo Trader",
            "hashed_password": hash_password("TradlyDemo2026!"),
            "role": "authenticated",
            "created_at": datetime.now(timezone.utc),
        }

    def register(self, req: UserCreate) -> TokenResponse:
        email = req.email.strip().lower()
        if email in self.users:
            raise ConflictError("A user with this email already exists")

        user_id = str(uuid.uuid4())
        hashed = hash_password(req.password)
        self.users[email] = {
            "id": user_id,
            "email": email,
            "name": req.name or email.split("@")[0],
            "hashed_password": hashed,
            "role": "authenticated",
            "created_at": datetime.now(timezone.utc),
        }

        token = create_access_token(user_id=user_id, email=email)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600,
            user=UserProfile(
                id=user_id,
                email=email,
                name=self.users[email]["name"],
                created_at=self.users[email]["created_at"],
            ),
        )

    def login(self, req: UserLogin) -> TokenResponse:
        email = req.email.strip().lower()
        user = self.users.get(email)
        if not user or not verify_password(req.password, user["hashed_password"]):
            raise AuthenticationError("Invalid email or password")

        token = create_access_token(user_id=user["id"], email=email)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600,
            user=UserProfile(
                id=user["id"],
                email=email,
                name=user["name"],
                created_at=user["created_at"],
            ),
        )

    def get_profile(self, user_id: str) -> UserProfile:
        for u in self.users.values():
            if u["id"] == user_id:
                return UserProfile(
                    id=u["id"],
                    email=u["email"],
                    name=u["name"],
                    created_at=u["created_at"],
                )
        raise AuthenticationError("User not found")


auth_service = AuthService()
