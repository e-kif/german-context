from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Literal


class UserBase(BaseModel):
    username: str
    email: EmailStr
    level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'A1'


class UserOut(UserBase):
    id: int
    last_login: datetime = None
    login_attempts: int = 0
    last_activity: datetime = None
    created_at: datetime = datetime.now()
    streak: int = 0


class UserIn(UserBase):
    password: str
