from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from data.database_manager import db_manager
from data.schemas import UserIn, UserOut

load_dotenv()
SECRET_KEY = os.getenv('OLD_SECRET_KEY')
REFRESH_SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('OLD_ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 1


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(username: str) -> UserIn | str:
    return db_manager.get_user_by_username(username)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        db_manager.add_user_login_attempts(user.id)
        return False
    db_manager.update_user_last_login(user.id)
    return user


def create_token(data: dict,
                 secret_key: str,
                 expiration_delta: timedelta | int = 15,
                 algorithm: str = ALGORITHM) -> str:
    to_encode = data.copy()
    if isinstance(expiration_delta, timedelta):
        expire = datetime.now(timezone.utc) + expiration_delta
    elif isinstance(expiration_delta, int):
        expire = datetime.now(timezone.utc) + timedelta(minutes=expiration_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt if isinstance(encoded_jwt, str) else encoded_jwt.decode('utf-8')


def create_access_token(data: dict,
                        expiration_delta: timedelta | int = 5,
                        secret_key: str = SECRET_KEY,
                        algorithm: str = ALGORITHM) -> str:
    access_token = create_token(data=data,
                                expiration_delta=expiration_delta,
                                secret_key=secret_key,
                                algorithm=algorithm)
    return access_token


def create_refresh_token(data: dict,
                         secret_key: str = REFRESH_SECRET_KEY,
                         expiration_delta: timedelta | int = 15,
                         algorithm: str = ALGORITHM) -> str:
    refresh_token = create_token(data=data,
                                 secret_key=secret_key,
                                 expiration_delta=expiration_delta,
                                 algorithm=algorithm)
    return refresh_token


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[UserOut, Depends(get_current_user)],
):
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def check_cookie(request: Request) -> str:
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Refresh token cookie not found')
    return refresh_token


async def decode_refresh_token(token: str, key: str, token_type: str) -> str:
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, [ALGORITHM])
        if payload['type'] != token_type:
            raise jwt.InvalidTokenError('Invalid token type')
        if datetime.utcnow() > datetime.utcfromtimestamp(payload['exp']):
            raise jwt.ExpiredSignatureError('Token has expired')
        return payload[key]
    except jwt.PyJWTError as e:
        print(f'Token decoding error: {e}')

if __name__ == '__main__':
    print(authenticate_user('string', 'string'))
