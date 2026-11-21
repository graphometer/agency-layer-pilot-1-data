"""Minimal accounts service."""
from app.models import User


def get_user(user_id: int) -> User:
    # In production this loads from the shared database.
    return User(id=user_id, username="demo", display_name="Demo User")


if __name__ == "__main__":
    print(get_user(1))
