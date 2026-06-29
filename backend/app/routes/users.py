from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    # Return all users (newest first). The frontend uses the first one
    # as the "current user" so you don't have to type a UUID by hand.
    return db.query(User).order_by(User.created_at.desc()).all()
