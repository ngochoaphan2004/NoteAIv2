import hmac
import hashlib
import base64
import json
import time
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from app.core.config import settings

logger = logging.getLogger("noteai_auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str = Field(..., description="Tên đăng nhập")
    password: str = Field(..., description="Mật khẩu truy cập")

class UserInfo(BaseModel):
    username: str
    role: str = "admin"

class LoginResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo

class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserInfo] = None

def create_access_token(username: str, role: str = "admin", expires_days: int = 30) -> str:
    """Sinh JWT token HS256 đơn giản không phụ thuộc thư viện bên ngoài"""
    header = {"alg": "HS256", "typ": "JWT"}
    now = time.time()
    payload = {
        "sub": username,
        "role": role,
        "iat": int(now),
        "exp": int(now + expires_days * 86400)
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(settings.AUTH_SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Xác thực và giải mã JWT token HS256"""
    if not token:
        return None
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(settings.AUTH_SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()

    pad_s = (4 - len(sig_b64) % 4) % 4
    try:
        actual_sig = base64.urlsafe_b64decode(sig_b64 + ("=" * pad_s))
    except Exception:
        return None

    if not hmac.compare_digest(expected_sig, actual_sig):
        return None

    pad_p = (4 - len(payload_b64) % 4) % 4
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + ("=" * pad_p)).decode())
    except Exception:
        return None

    if "exp" in payload and time.time() > payload["exp"]:
        return None

    return payload

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[UserInfo]:
    """Dependency trích xuất user từ Authorization Header nếu có"""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    payload = decode_access_token(token)
    if not payload:
        return None
    return UserInfo(username=payload.get("sub", "admin"), role=payload.get("role", "admin"))

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """
    Xác thực đăng nhập người dùng.
    Mặc định so khớp với AUTH_USERNAME và AUTH_PASSWORD trong cấu hình hệ thống (.env).
    """
    input_user = req.username.strip()
    input_pass = req.password.strip()

    valid_user = settings.AUTH_USERNAME.strip()
    valid_pass = settings.AUTH_PASSWORD.strip()

    is_user_ok = hmac.compare_digest(input_user.encode("utf-8"), valid_user.encode("utf-8"))
    is_pass_ok = hmac.compare_digest(input_pass.encode("utf-8"), valid_pass.encode("utf-8"))

    if not (is_user_ok and is_pass_ok):
        logger.warning(f"Đăng nhập thất bại: tên tài khoản hoặc mật khẩu không đúng cho '{input_user}'")
        raise HTTPException(
            status_code=401,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác."
        )

    expires_seconds = settings.AUTH_TOKEN_EXPIRE_DAYS * 86400
    token = create_access_token(
        username=input_user,
        role="admin",
        expires_days=settings.AUTH_TOKEN_EXPIRE_DAYS
    )

    logger.info(f"Người dùng '{input_user}' đăng nhập thành công.")
    return LoginResponse(
        status="success",
        access_token=token,
        token_type="bearer",
        expires_in=expires_seconds,
        user=UserInfo(username=input_user, role="admin")
    )

@router.get("/me", response_model=AuthStatusResponse)
def get_me(authorization: Optional[str] = Header(None)):
    """Kiểm tra trạng thái xác thực phiên làm việc hiện tại"""
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập đã hết hạn hoặc không hợp lệ.")
    return AuthStatusResponse(authenticated=True, user=user)

@router.post("/logout")
def logout():
    """Đăng xuất người dùng khỏi hệ thống"""
    return {"status": "success", "message": "Đã đăng xuất thành công."}
