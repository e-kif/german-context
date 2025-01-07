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


class UserInRole(UserIn):
    role: Literal['User', 'Manager', 'Admin'] = 'User'


class UserLogin(BaseModel):
    username: str
    password: str


class UserPatch(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] | None = None


class WordBase(BaseModel):
    word: str


class WordIn(WordBase):
    english: str | None = None
    topic: str | None = None
    example: str | None = None
    example_translation: str | None = None
    level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] | None = None
    word_type: Literal['Noun', 'Verb', 'Adjective',
                       'Pronoun', 'Preposition', 'Conjunction',
                       'Adverb', 'Article', 'Particle'] | None = None


class AdminWordOut(WordBase):
    id: int
    word_type: str
    english: str
    level: str
    example: str | None = None
    example_translation: str | None = None


class WordOut(AdminWordOut):
    topic: str


class WordPatch(WordIn):
    word: str | None = None


class TopicIn(BaseModel):
    name: str


class TopicOut(TopicIn):
    id: int
