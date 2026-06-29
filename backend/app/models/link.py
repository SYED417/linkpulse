from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # The foreign key column. ondelete="CASCADE" mirrors the rule we set
    # in SQL: delete a user and their links go too.
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_url = Column(Text, nullable=False)
    short_code = Column(String(20), unique=True, nullable=False)
    # Optional user-chosen slug. Unique (which also creates an index for the
    # fast lookups every redirect performs). index=True is explicit for clarity.
    custom_slug = Column(String(50), unique=True, nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    # The "many" side back to User, and the "one" side toward Click.
    user = relationship("User", back_populates="links")
    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")
