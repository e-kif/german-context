import datetime
import sqlalchemy.exc
from fastapi import FastAPI, Path, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from typing import Annotated, Any


from data.schemas import *
from data.models import User, session
from modules.security import (get_password_hash,
                              Token,
                              authenticate_user,
                              ACCESS_TOKEN_EXPIRE_MINUTES,
                              get_current_active_user,
                              create_access_token)


app = FastAPI()


@app.get("/")
async def home():
    return {'message': 'home'}


@app.get("/users")
async def get_users() -> list[UserOut]:
    users = session.query(User).all()
    return users


@app.get("/user/{user_id}", response_model=UserOut)
async def get_user(user_id: Annotated[int, Path(ge=0, title='User ID')]) -> Any:
    user = session.query(User).filter(User.id == user_id).one()
    return user


@app.post("/users")
async def add_user(user: UserIn) -> UserBase:
    db_user = User(username=user.username,
                   email=user.email,
                   created_at=datetime.datetime.now(),
                   streak=0,
                   level=user.level,
                   password=get_password_hash(user.password))
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.put("/user/{user_id}", response_model=UserOut | dict)
async def update_user(user_id: Annotated[int, Path(title='User ID', ge=1)], user: UserIn):
    update_user_encoded = jsonable_encoder(user)
    try:
        user = session.query(User).filter(User.id == user_id).one()
    except sqlalchemy.exc.NoResultFound:
        return {'error': f'User with id={user_id} not found.'}
    user = update_user_encoded
    return user


@app.delete("/user/{user_id}")
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)]):
    try:
        delete_user = session.query(User).filter(User.id == user_id).one()
    except sqlalchemy.exc.NoResultFound:
        return {'Error': f'No user with id={user_id}.'}
    session.delete(delete_user)
    session.commit()
    return {'Success': f'User {delete_user} was deleted successfully.'}


@app.post("/token")
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
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=UserBase)
async def read_users_me(
    current_user: Annotated[UserBase, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/words/")
async def read_own_items(
    current_user: Annotated[UserOut, Depends(get_current_active_user)],
):
    return [current_user]
