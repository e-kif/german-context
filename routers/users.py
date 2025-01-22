from fastapi import APIRouter, Depends
from typing import Annotated

from data.schemas import UserIn, UserOut, UserPatch, UserBase
from data.database_manager import db_manager
from modules.security import get_password_hash, get_current_active_user
from modules.utils import check_for_exception

home_routes = APIRouter(tags=['Home'])
users = APIRouter(prefix='/users', tags=['users'])


@home_routes.get('/')
async def home():
    return {'message': 'Welcome to the German-Context App!'}


# @users.get('')
# async def get_users() -> list[UserOut]:
#     return db_manager.get_users()


@users.post('')
async def add_user(user: UserIn) -> UserBase:
    new_user = db_manager.add_user(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    check_for_exception(new_user, 409)
    return new_user


@users.put('/me', response_model=UserOut)
async def update_user(user: UserIn,
                      current_user: Annotated[UserOut, Depends(get_current_active_user)]):
    updated_user = db_manager.update_user(
        user_id=current_user.id,
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    check_for_exception(updated_user, 404)
    return updated_user


@users.patch('/me', response_model=UserOut)
async def patch_user(user: UserPatch,
                     current_user: Annotated[UserOut, Depends(get_current_active_user)]):
    db_user = db_manager.get_user_by_id(current_user.id)
    check_for_exception(db_user, 404)
    stored_user_model = UserIn(**db_user.__dict__)
    update_data = user.model_dump(exclude_unset=True)
    updated_user = stored_user_model.model_copy(update=update_data)
    db_user_updated = await update_user(updated_user, current_user)
    return db_user_updated


@users.get('/me', response_model=UserOut)
async def read_users_me(current_user: Annotated[UserOut, Depends(get_current_active_user)]):
    return current_user


@users.delete('/me')
async def remove_self(current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> UserOut:
    db_user = db_manager.get_user_by_id(current_user.id)
    check_for_exception(db_user, 404)
    deleted_user = db_manager.delete_user(db_user.id)
    return deleted_user
