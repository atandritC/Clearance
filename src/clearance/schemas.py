from pydantic import BaseModel


class DemoUserResponse(BaseModel):
    id: int
    display_name: str
    role: str
    department: str
