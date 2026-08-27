from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CreateLinkRequest(BaseModel):
    original_url: str = Field(
        min_length=1,
        max_length=2048,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    custom_slug: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    expires_at: str | None = None

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
    )

    @field_validator("original_url")
    @classmethod
    def validate_original_url(cls, value: str) -> str:
        value = value.strip()

        try:
            url = HttpUrl(value)
        except ValueError:
            raise ValueError("لینک مقصد معتبر نیست.")

        if url.scheme not in {"http", "https"}:
            raise ValueError(
                "فقط لینک‌های HTTP و HTTPS قابل استفاده هستند."
            )

        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("عنوان لینک نمی‌تواند خالی باشد.")

        return value

    @field_validator("custom_slug")
    @classmethod
    def validate_custom_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not all(
            char.isascii()
            and (
                char.isalnum()
                or char in {"-", "_"}
            )
            for char in value
        ):
            raise ValueError(
                "Slug فقط می‌تواند شامل حروف انگلیسی، اعداد، - و _ باشد."
            )

        if value[0] in {"-", "_"}:
            raise ValueError(
                "Slug نمی‌تواند با - یا _ شروع شود."
            )

        if value[-1] in {"-", "_"}:
            raise ValueError(
                "Slug نمی‌تواند با - یا _ تمام شود."
            )

        return value

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, value: str | None) -> str | None:
        allowed_values = {"1d", "7d", "30d"}

        if value is None or value == "":
            return None

        if value not in allowed_values:
            raise ValueError(
                "تاریخ انقضا باید یکی از مقادیر 1d، 7d یا 30d باشد."
            )

        return value


class LinkResponse(BaseModel):
    id: UUID
    short_url: str
    original_url: str
    title: str
    clicks: int
    status: str
    created_at: datetime
    expires_at: datetime | None


class LinkSortOption(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    MOST_CLICKED = "most-clicked"
    LEAST_CLICKED = "least-clicked"


class LinkListItem(BaseModel):
    id: UUID
    short_url: str
    original_url: str
    title: str
    clicks: int
    status: str
    created_at: datetime
    expires_at: datetime | None


class LinkListResponse(BaseModel):
    items: list[LinkListItem]
    page: int
    limit: int
    total: int
    total_pages: int


class UpdateLinkRequest(BaseModel):
    original_url: str | None = None
    title: str | None = Field(default=None, max_length=255)
    custom_slug: str | None = None
    expires_at: str | None = None
    password: str | None = None


class AnalyticsChartItem(BaseModel):
    date: str
    clicks: int


class AnalyticsBreakdownItem(BaseModel):
    name: str
    clicks: int


class LinkAnalyticsResponse(BaseModel):
    short_url: str
    original_url: str

    total_clicks: int
    today_clicks: int
    average_clicks: float

    chart_data: list[AnalyticsChartItem]

    countries: list[AnalyticsBreakdownItem]
    devices: list[AnalyticsBreakdownItem]
    browsers: list[AnalyticsBreakdownItem]
    operating_systems: list[AnalyticsBreakdownItem]