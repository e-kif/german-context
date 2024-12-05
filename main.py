import datetime
import sqlalchemy.exc
from fastapi import FastAPI, Path, Response, status
from typing import Annotated, Any

from data.schemas import *
from data.models import User, session
# from data.database_manager import session

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
async def add_user(user: UserIn, response: Response) -> UserOut | dict:
    db_user = User(username=user.username,
                   email=user.email,
                   created_at=datetime.now(),
                   streak=0,
                   level=user.level,
                   password=user.password)
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    except sqlalchemy.exc.IntegrityError as e:
        error = [line for line in str(e).split('\n') if line.startswith('DETAIL')][0]
        response.status_code = status.HTTP_400_BAD_REQUEST
        session.rollback()
        return {'error': error}
    return db_user


@app.put("/user/{user_id}")
async def update_user(user_id: Annotated[int, Path(title='User ID', ge=1)]):
    pass


@app.delete("/user/{user_id}")
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)]):
    try:
        delete_user = session.query(User).filter(User.id == user_id).one()
    except sqlalchemy.exc.NoResultFound:
        return {'Error': f'No user with id={user_id}.'}
    session.delete(delete_user)
    session.commit()
    return {'Success': f'User {delete_user} was deleted successfully.'}
