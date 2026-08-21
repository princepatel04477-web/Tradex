import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.schemas.auth import UserRegister, UserLogin, TokenResponse

SECRET_KEY = "tradly-super-secret-jwt-key-for-local-dev-and-demo"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class AuthService:
    def __init__(self):
        # Demo user in memory
        self.users: Dict[str, dict] = {
            "trader@tradly.ai": {
                "id": "usr-001",
                "email": "trader@tradly.ai",
                "hashed_password": pwd_context.hash("tradly123"),
                "full_name": "Demo Forex Trader"
            }
        }

    def register(self, request: UserRegister) -> TokenResponse:
        if request.email in self.users:
            raise ValueError("User with this email already exists")

        user_id = str(uuid.uuid4())[:8]
        hashed = pwd_context.hash(request.password)
        self.users[request.email] = {
            "id": user_id,
            "email": request.email,
            "hashed_password": hashed,
            "full_name": request.full_name or request.email.split("@")[0]
        }
        return self._create_token(user_id, request.email)

    def login(self, request: UserLogin) -> TokenResponse:
        user = self.users.get(request.email)
        if not user or not pwd_context.verify(request.password, user["hashed_password"]):
            raise ValueError("Invalid email or password")
        return self._create_token(user["id"], user["email"])

    def _create_token(self, user_id: str, email: str) -> TokenResponse:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expires
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return TokenResponse(
            access_token=token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user_id,
            email=email
        )

# Global singleton
auth_service = AuthService()
