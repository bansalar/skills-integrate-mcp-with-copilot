import hashlib
import hmac
import secrets

PASSWORD_ITERATIONS = 310_000


def hash_password(password: str) -> dict[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS
    ).hex()
    return {"salt": salt, "password_hash": digest}


def verify_password(password: str, teacher: dict[str, str]) -> bool:
    salt = teacher.get("salt", "")
    expected_hash = teacher.get("password_hash", "")
    if not salt or not expected_hash:
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS
    ).hex()
    return hmac.compare_digest(candidate_hash, expected_hash)