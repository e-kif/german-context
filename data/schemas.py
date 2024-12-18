import datetime
from pydantic import BaseModel, EmailStr
from typing import Literal


class UserBase(BaseModel):
    username: str
    email: EmailStr
    level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'A1'


class UserOut(UserBase):
    id: int
    last_login: datetime.datetime | None = None
    login_attempts: int = 0
    last_activity: datetime.datetime | None = None
    created_at: datetime.datetime = datetime.datetime.now()
    streak: int = 0


class UserIn(UserBase):
    password: str


class UserPatch(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] | None = None

class WordIn(BaseModel):
    word: str


class WordOut(WordIn):
    id: int
    word_type_id: int
    english: str
    level: str


class TopicIn(BaseModel):
    name: str
    description: str | None = None


class TopicOut(TopicIn):
    id: int
