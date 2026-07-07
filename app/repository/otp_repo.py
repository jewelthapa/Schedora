import secrets
import string
from datetime import datetime, timedelta

from app.database import get_connection


OTP_LENGTH = 6
OTP_TTL_MINUTES = 5
MAX_VERIFY_ATTEMPTS = 3


def _generate_code():
    """Generate a 6-digit numeric OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))


def create_for_user(user_id, purpose="login"):
    """Invalidate any existing OTPs for this user + purpose, then create a new one.
    Returns the plaintext code (so we can send it via email/console)."""
    code = _generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Invalidate old codes so a user can't rush multiple pending OTPs
            cursor.execute(
                "UPDATE otp_codes SET is_used = TRUE WHERE user_id = %s AND purpose = %s AND is_used = FALSE",
                (user_id, purpose),
            )
            # Insert the new code
            cursor.execute(
                """INSERT INTO otp_codes (user_id, code, purpose, expires_at, is_used)
                   VALUES (%s, %s, %s, %s, FALSE)""",
                (user_id, code, purpose, expires_at),
            )
            conn.commit()
    finally:
        conn.close()

    return code


def verify_and_consume(user_id, code_attempt, purpose="login"):
    """Try to consume a code for this user. Returns:
       'ok'         - code matches, now consumed
       'expired'    - code expired
       'invalid'    - code doesn't match, attempts still available
       'exhausted'  - too many wrong attempts, code invalidated
       'missing'    - no pending code exists
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, code, expires_at, attempts
                   FROM otp_codes
                   WHERE user_id = %s AND purpose = %s AND is_used = FALSE
                   ORDER BY id DESC LIMIT 1""",
                (user_id, purpose),
            )
            row = cursor.fetchone()

            if row is None:
                return "missing"

            if row["expires_at"] < datetime.utcnow():
                cursor.execute(
                    "UPDATE otp_codes SET is_used = TRUE WHERE id = %s",
                    (row["id"],),
                )
                conn.commit()
                return "expired"

            if row["code"] != code_attempt:
                new_attempts = (row["attempts"] or 0) + 1
                if new_attempts >= MAX_VERIFY_ATTEMPTS:
                    cursor.execute(
                        "UPDATE otp_codes SET is_used = TRUE, attempts = %s WHERE id = %s",
                        (new_attempts, row["id"]),
                    )
                    conn.commit()
                    return "exhausted"
                cursor.execute(
                    "UPDATE otp_codes SET attempts = %s WHERE id = %s",
                    (new_attempts, row["id"]),
                )
                conn.commit()
                return "invalid"

            # Success — mark as used
            cursor.execute(
                "UPDATE otp_codes SET is_used = TRUE WHERE id = %s",
                (row["id"],),
            )
            conn.commit()
            return "ok"
    finally:
        conn.close()