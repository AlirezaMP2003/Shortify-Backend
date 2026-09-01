from pydantic import BaseModel


class DashboardChartItem(BaseModel):
    date: str
    clicks: int


class DashboardOverviewResponse(BaseModel):
    total_links: int
    total_clicks: int

    active_links: int
    expired_links: int

    clicks_last_7_days: list[DashboardChartItem]