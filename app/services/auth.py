from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    generate_reset_code,
    hash_password,
    verify_password,
)
from app.models import User


# Temporary in-memory storage for MVP.
# This will later be replaced with a proper
# password reset token table + email service.
_password_reset_tokens: dict[str, str] = {}


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    return (
        db.query(User)
        .filter(User.email == email.lower())
        .first()
    )


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str,
) -> User:

    email = email.lower()

    existing_user = get_user_by_email(
        db,
        email,
    )

    if existing_user:
        raise ValueError(
            "این ایمیل قبلاً ثبت شده است."
        )

    user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:

    user = get_user_by_email(
        db,
        email,
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(
        str(user.id)
    )


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> None:

    if not verify_password(
        current_password,
        user.password_hash,
    ):
        raise ValueError(
            "رمز عبور فعلی اشتباه است."
        )

    user.password_hash = hash_password(
        new_password
    )

    db.commit()


def create_password_reset_request(
    db: Session,
    email: str,
) -> None:

    user = get_user_by_email(
        db,
        email,
    )

    # Do not reveal whether the email exists.
    if user is None:
        return

    reset_code = generate_reset_code()

    reset_token = create_password_reset_token(
        str(user.id),
        reset_code,
    )

    _password_reset_tokens[email.lower()] = reset_token

    print()
    print("=" * 50)
    print("PASSWORD RESET CODE")
    print(f"Email: {email}")
    print(f"Code: {reset_code}")
    print("Expires: 10 minutes")
    print("=" * 50)
    print()


def reset_user_password(
    db: Session,
    email: str,
    reset_code: str,
    new_password: str,
) -> None:

    email = email.lower()

    reset_token = _password_reset_tokens.get(email)

    if reset_token is None:
        raise ValueError(
            "کد بازیابی معتبر نیست یا منقضی شده است."
        )

    try:
        payload = decode_password_reset_token(
            reset_token
        )

    except Exception:
        _password_reset_tokens.pop(
            email,
            None,
        )

        raise ValueError(
            "کد بازیابی معتبر نیست یا منقضی شده است."
        )

    if payload.get("type") != "password_reset":
        raise ValueError(
            "کد بازیابی معتبر نیست."
        )

    if payload.get("code") != reset_code:
        raise ValueError(
            "کد بازیابی اشتباه است."
        )

    user_id = payload.get("sub")

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise ValueError(
            "کاربر پیدا نشد."
        )

    user.password_hash = hash_password(
        new_password
    )

    db.commit()

    # Make the reset code unusable after successful reset.
    _password_reset_tokens.pop(
        email,
        None,
    )



def update_user_profile(
    db: Session,
    user: User,
    name: str,
    email: str,
) -> User:

    normalized_email = email.strip().lower()

    existing_user = (
        db.query(User)
        .filter(
            User.email.ilike(normalized_email),
            User.id != user.id,
        )
        .first()
    )

    if existing_user:
        raise ValueError(
            "این ایمیل قبلاً استفاده شده است."
        )

    user.name = name.strip()
    user.email = normalized_email

    db.commit()
    db.refresh(user)

    return user


def delete_user_account(
    db: Session,
    user: User,
) -> None:
    db.delete(user)
    db.commit()