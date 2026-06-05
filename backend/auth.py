import os, datetime, secrets
from typing import Optional

import bcrypt
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError

from backend.database import conn, init_db, delete_user_journal, IntegrityError

ALGORITHM   = "HS256"
EXPIRE_DAYS = 30

# SECRET_KEY 로드 순서: 환경변수 → 파일 → 신규 생성 (재시작해도 토큰 유지)
_HF_DATA  = "/data"
_KEY_FILE = os.path.join(_HF_DATA, ".secret_key") if os.path.isdir(_HF_DATA) else os.path.join(os.path.dirname(__file__), ".secret_key")

def _load_secret_key() -> str:
    env = os.environ.get("SECRET_KEY")
    if env:
        return env
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "r") as f:
            key = f.read().strip()
            if key:
                return key
    key = secrets.token_hex(32)
    with open(_KEY_FILE, "w") as f:
        f.write(key)
    return key

SECRET_KEY = _load_secret_key()


def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _verify_pw(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


_bearer = HTTPBearer(auto_error=False)
router  = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)):
    if not creds:
        raise HTTPException(401, "인증이 필요합니다")
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "토큰이 유효하지 않습니다")
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(401, "사용자를 찾을 수 없습니다")
    return dict(row)


class RegisterForm(BaseModel):
    username: str
    email:    str
    password: str

class LoginForm(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(form: RegisterForm):
    if len(form.username.strip()) < 2:
        raise HTTPException(400, "이름은 2자 이상이어야 합니다")
    if len(form.password) < 6:
        raise HTTPException(400, "비밀번호는 6자 이상이어야 합니다")
    try:
        with conn() as c:
            c.execute(
                "INSERT INTO users (username, email, hashed_password, created_at) VALUES (?,?,?,?)",
                (form.username.strip(), form.email.strip(),
                 _hash_pw(form.password), datetime.datetime.now().isoformat()),
            )
        return {"ok": True}
    except IntegrityError:
        raise HTTPException(400, "이미 사용 중인 이름 또는 이메일입니다")


@router.post("/login")
def login(form: LoginForm):
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE username = ?",
                        (form.username.strip(),)).fetchone()
    if not row or not _verify_pw(form.password, row["hashed_password"]):
        raise HTTPException(401, "이름 또는 비밀번호가 올바르지 않습니다")
    exp   = datetime.datetime.utcnow() + datetime.timedelta(days=EXPIRE_DAYS)
    token = jwt.encode({"sub": str(row["id"]), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer",
            "username": row["username"], "user_id": row["id"]}


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    return {"id": user["id"], "username": user["username"], "email": user["email"]}


@router.delete("/me")
def delete_account(user=Depends(get_current_user)):
    delete_user_journal(user["id"])
    with conn() as c:
        c.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    return {"ok": True}


# ── 비밀번호 재설정 ────────────────────────────────────────────────────────────

class ResetPasswordForm(BaseModel):
    email:        str
    new_password: str


@router.post("/reset-password")
def reset_password(form: ResetPasswordForm):
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE email = ?", (form.email.strip(),)).fetchone()
    if not row:
        raise HTTPException(404, "해당 이메일로 가입된 계정을 찾을 수 없습니다.")
    if len(form.new_password) < 6:
        raise HTTPException(400, "비밀번호는 6자 이상이어야 합니다")
    with conn() as c:
        c.execute("UPDATE users SET hashed_password = ? WHERE id = ?",
                  (_hash_pw(form.new_password), row["id"]))
    return {"ok": True}
