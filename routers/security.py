from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
import datetime

from modules.security import Token, authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

security = APIRouter(tags=['security'])


@security.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expiration_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


from fastapi.responses import JSONResponse
from modules.security import create_access_token, authenticate_user, create_refresh_token, check_cookie
from data.schemas import UserLogin


@security.post("/login")
async def login_for_access_token(user: UserLogin):
    if user.username and user.password:
        db_user = authenticate_user(user.username, user.password)
        if db_user:
            token = create_access_token(data={'sub': db_user.username},
                                        expiration_delta=datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
            refresh_token = create_refresh_token(data={'sub': db_user.username, 'id': db_user.id})
            response = JSONResponse({'token': token}, status_code=200)
            response.set_cookie(key='refresh-Token', value=refresh_token)
            return response
    return JSONResponse({'msg': 'Invalid Credentials'}, status_code=403)

@security.post("/refresh")
async def refresh_token(refresh_token: str = Depends(check_cookie)):
    pass
