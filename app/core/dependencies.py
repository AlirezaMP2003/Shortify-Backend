import jwt

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="احراز هویت نامعتبر است.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if not access_token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            access_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "access":
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است.",
        )

    return user