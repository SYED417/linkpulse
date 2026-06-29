import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Link, User
from app.schemas.link import LinkCreate, LinkResponse

# A router groups related endpoints. prefix="/api" means every route here
# starts with /api, so this one becomes POST /api/links.
router = APIRouter(prefix="/api", tags=["links"])

# Characters allowed in a short code: a-z, A-Z, 0-9.
ALPHABET = string.ascii_letters + string.digits


def generate_short_code(db: Session, length: int = 6) -> str:
    """Generate a random code and keep trying until it's unused."""
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        # Check the DB; if no link has this code, it's safe to use.
        existing = db.query(Link).filter(Link.short_code == code).first()
        if existing is None:
            return code


@router.get("/links", response_model=list[LinkResponse])
def list_links(db: Session = Depends(get_db)):
    # All links, newest first — used to populate the table in the UI.
    return db.query(Link).order_by(Link.created_at.desc()).all()


@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)):
    # 1. Make sure the user actually exists (foreign key safety + clear error).
    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 2. Generate a guaranteed-unique short code.
    short_code = generate_short_code(db)

    # 3. Build the new Link row. (id, created_at, is_active fill in by default.)
    new_link = Link(
        user_id=payload.user_id,
        original_url=str(payload.original_url),
        short_code=short_code,
    )

    # 4. Save it: stage -> commit -> refresh to pull DB-generated values back.
    db.add(new_link)
    db.commit()
    db.refresh(new_link)

    # 5. FastAPI converts this object into JSON shaped like LinkResponse.
    return new_link
