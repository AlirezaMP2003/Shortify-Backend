import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, text, Index
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LinkClick(Base):
    __tablename__ = "link_clicks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
    )

    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    device: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    browser: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    os: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    referer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    link: Mapped["Link"] = relationship(
        "Link",
        back_populates="clicks",
    )

    __table_args__ = (
        Index(
            "ix_link_clicks_link_clicked",
            "link_id",
            "clicked_at",
        ),
    )