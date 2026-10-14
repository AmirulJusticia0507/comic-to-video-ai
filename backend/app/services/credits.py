from sqlalchemy.orm import Session

from app.models import User


class InsufficientCreditsError(Exception):
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"insufficient credits: required {required}, available {available}")


def deduct_credits(db: Session, user: User, amount: int = 1) -> None:
    if user.credits < amount:
        raise InsufficientCreditsError(amount, user.credits)
    user.credits -= amount
    db.flush()
