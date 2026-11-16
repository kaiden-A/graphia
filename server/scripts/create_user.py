from __future__ import annotations

import argparse

from sqlalchemy import select

from app.services.auth_services import normalize_email
from core.database import SessionLocal
from core.logging import configure_logging
from core.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a placeholder user row; the first Zitadel login adopts it by email."
    )
    parser.add_argument("email")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    configure_logging()
    email = normalize_email(args.email)

    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            raise SystemExit("A user with that email already exists.")
        user = User(email=email, name=args.name, password_hash=None)
        db.add(user)
        db.commit()
        print(f"Created placeholder {user.email} ({user.id})")
        print("The first Zitadel login with this email will adopt the row.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
