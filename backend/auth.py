import os, datetime, secrets, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
    init_db()
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
    init_db()
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
    init_db()
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

def _send_reset_email(to_email: str, reset_url: str):
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    if not smtp_user or not smtp_pass:
        raise ValueError("SMTP_USER / SMTP_PASS 환경변수가 설정되지 않았습니다")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[Inner Gallery] 비밀번호 재설정"
    msg["From"]    = f"Inner Gallery <{smtp_user}>"
    msg["To"]      = to_email

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#FAF7F2;border-radius:12px">
      <h2 style="font-size:20px;color:#1A0800;margin-bottom:8px">비밀번호 재설정</h2>
      <p style="color:#6B5E52;font-size:14px;line-height:1.8">
        아래 버튼을 클릭해 새 비밀번호를 설정하세요.<br>링크는 <strong>1시간</strong> 후 만료됩니다.
      </p>
      <a href="{reset_url}" style="display:inline-block;margin:24px 0;padding:14px 28px;background:#1A0800;color:#C9A84C;text-decoration:none;border-radius:6px;font-size:14px;letter-spacing:1px">
        비밀번호 재설정하기
      </a>
      <p style="color:#9C8E84;font-size:11px">본인이 요청하지 않은 경우 이 메일을 무시하세요.</p>
      <p style="color:#C9A84C;font-size:10px;letter-spacing:2px;margin-top:24px">INNER GALLERY</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.ehlo()
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.sendmail(smtp_user, to_email, msg.as_string())


class ForgotPasswordForm(BaseModel):
    email: str

class ResetPasswordForm(BaseModel):
    token:        str
    new_password: str


@router.post("/forgot-password")
def forgot_password(form: ForgotPasswordForm):
    init_db()
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE email = ?", (form.email.strip(),)).fetchone()
    if not row:
        return {"ok": True}  # 이메일 존재 여부 노출 방지

    token   = secrets.token_urlsafe(32)
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()

    with conn() as c:
        c.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (row["id"],))
        c.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?,?,?)",
            (row["id"], token, expires),
        )

    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    reset_url    = f"{frontend_url}/reset-password?token={token}"

    try:
        _send_reset_email(form.email.strip(), reset_url)
    except Exception as e:
        raise HTTPException(500, f"이메일 발송 실패: {e}")

    return {"ok": True}


@router.post("/reset-password")
def reset_password(form: ResetPasswordForm):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    with conn() as c:
        row = c.execute(
            "SELECT * FROM password_reset_tokens WHERE token = ? AND used = 0 AND expires_at > ?",
            (form.token, now),
        ).fetchone()
    if not row:
        raise HTTPException(400, "링크가 유효하지 않거나 만료되었습니다.")
    if len(form.new_password) < 6:
        raise HTTPException(400, "비밀번호는 6자 이상이어야 합니다")

    with conn() as c:
        c.execute("UPDATE users SET hashed_password = ? WHERE id = ?",
                  (_hash_pw(form.new_password), row["user_id"]))
        c.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (form.token,))

    return {"ok": True}


@router.get("/verify-reset-token")
def verify_reset_token(token: str):
    init_db()
    now = datetime.datetime.utcnow().isoformat()
    with conn() as c:
        row = c.execute(
            "SELECT id FROM password_reset_tokens WHERE token = ? AND used = 0 AND expires_at > ?",
            (token, now),
        ).fetchone()
    return {"valid": bool(row)}
