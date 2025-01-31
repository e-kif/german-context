from fastapi import APIRouter, Depends
from typing import Annotated

from data.schemas import UserIn, UserOut, UserPatch, UserBase
from data.database_manager import db_manager
from modules.security import get_password_hash, get_current_active_user
from modules.utils import check_for_exception, raise_exception

home_routes = APIRouter(tags=['Home'])
users = APIRouter(prefix='/users', tags=['users'])


@home_routes.get('/', summary='Welcome message')
async def home():
    """## Shows welcome message with the _App name_"""
    return {'message': 'Welcome to the German-Context App!'}


# @users.get('')
# async def get_users() -> list[UserOut]:
#     return db_manager.get_users()


@users.post('', summary='Add a new user')
async def add_user(user: UserIn) -> UserBase:
    """## Create a new user
    If creating the very first user, he/she will be assigned to the *Admin* role. Otherwise - *User*.

     **Required** body fields:
    - _username_ (should be unique)
    - _email_ (should be unique)
    - _password_

     **Optional** body field:
    - _level_ (user's German level. Default value is _A1_)
    """
    new_user = db_manager.add_user(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    check_for_exception(new_user, 409)
    return new_user


@users.put('/me', summary="Update current user's info")
async def update_user(user: UserIn,
                      current_user: Annotated[UserOut, Depends(get_current_active_user)]
                      ) -> UserOut:
    """## Update info for the current logged user
    All fields are required.
    """
    updated_user = db_manager.update_user(
        user_id=current_user.id,
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    if isinstance(updated_user, str) and 'was not found' in updated_user:
        raise_exception(404, updated_user)
    check_for_exception(updated_user, 409)
    return updated_user


@users.patch('/me', summary="Update current user's info")
async def patch_user(user: UserPatch,
                     current_user: Annotated[UserOut, Depends(get_current_active_user)]
                     ) -> UserOut:
    """## Update info for the current logged user
    All fields are optional. At least one field should be provided.
    """
    db_user = db_manager.get_user_by_id(current_user.id)
    check_for_exception(db_user, 404)
    stored_user_model = UserIn(**db_user.__dict__)
    update_data = user.model_dump(exclude_unset=True)
    updated_user = stored_user_model.model_copy(update=update_data)
    db_user_updated = await update_user(updated_user, current_user)
    if isinstance(db_user_updated, str) and 'was not found' in db_user_updated:
        raise_exception(404, db_user_updated)
    check_for_exception(db_user_updated, 409)
    return db_user_updated


@users.get('/me', summary="Show current user's info")
async def read_users_me(current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> UserOut:
    """## Show info of the current logged user"""
    return current_user


@users.delete('/me', summary='Delete current user')
async def remove_self(current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> UserOut:
    """## Delete the current logged user from the App
    This is **irreversible action**. After this:
    1. User's info will be deleted from the App.
    1. All user's words and topics will be deleted as well.

    As a result the user **will not** be able to:
    - Login.
    - Restore words and topics information even after registering again with the same username and email.
    """
    db_user = db_manager.get_user_by_id(current_user.id)
    check_for_exception(db_user, 404)
    deleted_user = db_manager.delete_user(db_user.id)
    return deleted_user
