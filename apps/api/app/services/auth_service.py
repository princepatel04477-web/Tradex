"""Authentication service supporting JWT access token issuance and password verification (FG-6, NFR-S1)."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from app.core.errors import AuthenticationError, ConflictError, ForbiddenError
from app.core.logging import logger
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.base import get_db_pool
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserProfile

# Secret master invitation code required to create any new user account
MASTER_INVITE_CODE = "TRADLY_PRINCE_2026"


class AuthService:
    def __init__(self):
        self.in_memory_users: Dict[str, dict] = {}
        # Seed VIP Master Account
        vip_id = "9dca1422-efd3-4f9f-a96f-b9a34d6b4ccd"
        self.in_memory_users["princepatel01258@gmail.com"] = {
            "id": vip_id,
            "email": "princepatel01258@gmail.com",
            "name": "Prince Patel",
            "hashed_password": hash_password("Prince_1258"),
            "role": "admin",
            "created_at": datetime.now(timezone.utc),
        }

    async def register(self, req: UserCreate) -> TokenResponse:
        # Require valid administrator invite code
        if not req.invite_code or req.invite_code.strip() != MASTER_INVITE_CODE:
            raise ForbiddenError("Registration is restricted. A valid master administrator invitation code is required.")

        email = req.email.strip().lower()
        pool = get_db_pool()

        if pool:
            try:
                async with pool.acquire() as conn:
                    existing = await conn.fetchrow(
                        "SELECT id FROM users WHERE email = $1", email
                    )
                    if existing:
                        raise ConflictError("A user with this email already exists")

                    user_id = str(uuid.uuid4())
                    hashed = hash_password(req.password)
                    name = req.name or email.split("@")[0]
                    now = datetime.now(timezone.utc)

                    await conn.execute(
                        """
                        INSERT INTO users (id, email, name, hashed_password, role, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        uuid.UUID(user_id),
                        email,
                        name,
                        hashed,
                        "authenticated",
                        now,
                        now,
                    )

                    token = create_access_token(user_id=user_id, email=email)
                    return TokenResponse(
                        access_token=token,
                        token_type="bearer",
                        expires_in=3600,
                        user=UserProfile(
                            id=user_id,
                            email=email,
                            name=name,
                            created_at=now,
                        ),
                    )
            except (ConflictError, ForbiddenError):
                raise
            except Exception as e:
                logger.warning(f"Database user insert failed ({e}), falling back to in-memory store")

        # Fallback to in-memory store
        if email in self.in_memory_users:
            raise ConflictError("A user with this email already exists")

        user_id = str(uuid.uuid4())
        hashed = hash_password(req.password)
        now = datetime.now(timezone.utc)
        name = req.name or email.split("@")[0]

        self.in_memory_users[email] = {
            "id": user_id,
            "email": email,
            "name": name,
            "hashed_password": hashed,
            "role": "authenticated",
            "created_at": now,
        }

        token = create_access_token(user_id=user_id, email=email)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600,
            user=UserProfile(
                id=user_id,
                email=email,
                name=name,
                created_at=now,
            ),
        )

    async def login(self, req: UserLogin) -> TokenResponse:
        email = req.email.strip().lower()
        pool = get_db_pool()

        if pool:
            try:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT id, email, name, hashed_password, created_at FROM users WHERE email = $1",
                        email,
                    )
                    if row:
                        if not verify_password(req.password, row["hashed_password"]):
                            raise AuthenticationError("Invalid email or password")

                        user_id = str(row["id"])
                        token = create_access_token(user_id=user_id, email=email)
                        return TokenResponse(
                            access_token=token,
                            token_type="bearer",
                            expires_in=3600,
                            user=UserProfile(
                                id=user_id,
                                email=row["email"],
                                name=row["name"],
                                created_at=row["created_at"],
                            ),
                        )
            except AuthenticationError:
                raise
            except Exception as e:
                logger.warning(f"Database login query failed ({e}), falling back to in-memory store")

        # Fallback to in-memory store
        user = self.in_memory_users.get(email)
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

    async def get_profile(self, user_id: str) -> UserProfile:
        pool = get_db_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT id, email, name, created_at FROM users WHERE id = $1",
                        uuid.UUID(user_id),
                    )
                    if row:
                        return UserProfile(
                            id=str(row["id"]),
                            email=row["email"],
                            name=row["name"],
                            created_at=row["created_at"],
                        )
            except Exception as e:
                logger.warning(f"Database get_profile query failed ({e})")

        for u in self.in_memory_users.values():
            if u["id"] == user_id:
                return UserProfile(
                    id=u["id"],
                    email=u["email"],
                    name=u["name"],
                    created_at=u["created_at"],
                )
        raise AuthenticationError("User not found")


auth_service = AuthService()
