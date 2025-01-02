from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from typing import Annotated
import datetime

from modules.security import authenticate_user, create_access_token, \
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, create_refresh_token, check_cookie, decode_refresh_token

security = APIRouter(tags=['security'])


@security.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> JSONResponse:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username},
                                       expiration_delta=access_token_expires)
    refresh_token_ = create_refresh_token(data={'sub': user.username, 'type': 'refresh'})
    response = JSONResponse(content={'access_token': access_token, 'token_type': 'bearer'})
    response.set_cookie(key='refresh_token', value=refresh_token_, httponly=True)
    return response


@security.post("/refresh")
async def refresh_token(token: str = Depends(check_cookie)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='No refresh token')
    decoded_token = decode_refresh_token(token, 'sub', 'refresh')
    if not decoded_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid refresh token')
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='User does not exist.')
    access_token = create_access_token(data={'sub': user.username})
    data = {'access_token': access_token, 'token_type': 'bearer'}
    return JSONResponse(content=data, status_code=200)
