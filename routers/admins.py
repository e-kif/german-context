from fastapi import APIRouter, Path, HTTPException, status, Depends
from typing import Annotated

from data.schemas import UserOut, UserIn, UserPatch, UserInRole, WordOut
from data.database_manager import db_manager
from modules.security import get_current_user, get_password_hash
import modules.serialization as serialization


def is_user_admin(current_user: Annotated[UserOut, Depends(get_current_user)]) -> bool:
    if not db_manager.check_user_role(current_user.id, 'Admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'User "{current_user.username}" is not an Admin. Not enough privileges.')
    return True


admin_users = APIRouter(prefix='/admin/users', dependencies=[Depends(is_user_admin)], tags=['admin_users'])
admin_words = APIRouter(prefix='/admin/words', dependencies=[Depends(is_user_admin)], tags=['admin_words'])
admin_user_words = APIRouter(prefix='/admin/user', dependencies=[Depends(is_user_admin)], tags=['admin_user_words'])


@admin_users.get('')
async def get_users() -> list[UserOut]:
    return db_manager.get_users()


@admin_users.post('/add')
async def add_user(user: UserInRole) -> UserOut:
    new_user = db_manager.add_user(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    if isinstance(new_user, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=new_user)
    db_manager.assign_user_role(new_user.id, user.role)
    return new_user


@admin_users.get('{user_id}')
async def get_user(user_id: Annotated[int, Path(ge=1, title='User ID')]) -> UserOut:
    user = db_manager.get_user_by_id(user_id)
    if isinstance(user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=user)
    return user


@admin_users.delete('/{user_id}')
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)]):
    delete_user = db_manager.delete_user(user_id)
    if isinstance(delete_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=delete_user)
    return {'Success': f'User {delete_user} was deleted successfully.'}


@admin_users.put('/{user_id}')
async def update_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                      user: UserIn) -> UserOut:
    updated_user = db_manager.update_user(
        user_id=user_id,
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    if isinstance(updated_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=updated_user)
    return updated_user


@admin_users.patch('/{user_id}')
async def patch_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                     user: UserPatch) -> UserOut:
    db_user = db_manager.get_user_by_id(user_id)
    if isinstance(db_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user)
    stored_user_model = UserIn(**db_user.__dict__)
    update_data = user.model_dump(exclude_unset=True)
    updated_user = stored_user_model.model_copy(update=update_data)
    db_user_updated = await update_user(user_id, updated_user)
    return db_user_updated


@admin_user_words.get('/{user_id}/words')
async def get_user_words(user_id: Annotated[int, Path(title='User ID', ge=1)]) -> list[WordOut]:
    user_words = db_manager.get_user_words(user_id)
    return serialization.word_out_list_from_user_words(user_words)
