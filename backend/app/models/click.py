from sqlalchemy import Column, String, Text, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship

from app.db.database import Base


class Click(Base):
    __tablename__ = "clicks"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    link_id = Column(
        UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
    )
    clicked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    country = Column(String(2))        # nullable: not always known
    device_type = Column(String(20))   # nullable
    referrer = Column(Text)            # nullable
    ip_address = Column(INET)          # nullable; PostgreSQL IP type

    link = relationship("Link", back_populates="clicks")
