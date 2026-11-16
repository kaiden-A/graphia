from __future__ import annotations

import argparse
import getpass

from app.services.auth_services import normalize_email
from core.database import SessionLocal
from core.logging import configure_logging
from core.models.user import User
from core.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Graphia user without using signup.")
    parser.add_argument("email")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    configure_logging()
    email = normalize_email(args.email)
    password = getpass.getpass("Password: ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).one_or_none()
        if existing is not None:
            raise SystemExit("A user with that email already exists.")
        user = User(email=email, name=args.name, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        print(f"Created {user.email} ({user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
