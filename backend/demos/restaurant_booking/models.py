from pydantic import BaseModel
from typing import Optional

class ConnectionRequest(BaseModel):
    """Defines what data we need to connect to voice room"""
    participant_name: Optional[str] = "Customer"


class ConnectionResponse(BaseModel):
    """LiveKit connection details returned to frontend"""
    server_url: str
    room_name: str
    participant_name: str
    participant_token: str


class MenuResponse(BaseModel):
    """Menu items response"""
    menu: dict
    categories: list[str]


class ServiceInfo(BaseModel):
    """Health check response"""
    status: str
    service: str
    description: str
