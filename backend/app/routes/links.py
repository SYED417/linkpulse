import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Link, User
from app.routes.auth import get_current_user
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
        existing = db.query(Link).filter(Link.short_code == code).first()
        if existing is None:
            return code


@router.get("/links", response_model=list[LinkResponse])
def list_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only the authenticated user's own links, newest first.
    return (
        db.query(Link)
        .filter(Link.user_id == current_user.id)
        .order_by(Link.created_at.desc())
        .all()
    )


@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_link(
    payload: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # The owner is taken from the JWT, never from the request body.
    custom_slug = payload.custom_slug  # already sanitized/validated by Pydantic
    if custom_slug is not None:
        taken = (
            db.query(Link.id)
            .filter(
                (Link.custom_slug == custom_slug) | (Link.short_code == custom_slug)
            )
            .first()
        )
        if taken is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slug already taken.",
            )

    short_code = generate_short_code(db)
    new_link = Link(
        user_id=current_user.id,
        original_url=str(payload.original_url),
        short_code=short_code,
        custom_slug=custom_slug,
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link
