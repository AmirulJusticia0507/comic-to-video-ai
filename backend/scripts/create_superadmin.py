from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User


def main() -> None:
    settings = get_settings()
    if not settings.superadmin_email or not settings.superadmin_password:
        raise RuntimeError("SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must be set")
    if len(settings.superadmin_password) < 12:
        raise RuntimeError("SUPERADMIN_PASSWORD must be at least 12 characters")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.superadmin_email).one_or_none()
        if user is None:
            user = User(
                email=settings.superadmin_email,
                hashed_password=hash_password(settings.superadmin_password),
                is_superadmin=True,
            )
            db.add(user)
        else:
            user.hashed_password = hash_password(settings.superadmin_password)
            user.is_superadmin = True
        db.commit()
        print(f"Superadmin ready: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
