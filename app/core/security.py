from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher
from app.core.config import settings

# Prefer modern Argon2 hashes while retaining verification support for bcrypt
# hashes already present in the supplied PostgreSQL dump.
password_hash = PasswordHash((Argon2Hasher(), BcryptHasher()))
ALGORITHM = "HS256"
COOKIE_NAME = "learning_gap_session"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try: return password_hash.verify(password, hashed)
    except Exception: return False

def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(hours=12)}, settings.jwt_secret, algorithm=ALGORITHM)

def decode_token(token: str):
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
