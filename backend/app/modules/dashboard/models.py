from typing import Optional

from pydantic import BaseModel


class DashboardRow(BaseModel):
    tutor_id: int
    name: str
    sessions_count: int
    avg_total: Optional[float]
    last_session: Optional[str]
