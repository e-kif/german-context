from fastapi import APIRouter, Path, HTTPException, status, Depends
from typing import Annotated, Any

from data.schemas import UserOut, UserIn, UserPatch, UserInRole
from data.database_manager import db_manager
from modules.security import get_current_user, get_password_hash

admins = APIRouter(tags=["admins"])

not_admin_exception = HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail='')


def is_user_admin(user: UserOut) -> bool:
    if not db_manager.check_user_role(user.id, 'Admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'User "{user.username}" is not an Admin. Not enough privileges.')
    return True


@admins.post("/user/add")
async def add_user(user: UserInRole,
                   current_user: Annotated[UserOut, Depends(get_current_user)]) -> UserOut:
    is_user_admin(current_user)
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


@admins.get("/user/{user_id}", response_model=UserOut)
async def get_user(user_id: Annotated[int, Path(ge=0, title='User ID')],
                   current_user: Annotated[UserOut, Depends(get_current_user)]) -> Any:
    is_user_admin(current_user)
    user = db_manager.get_user_by_id(user_id)
    if isinstance(user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=user)
    return user


@admins.delete("/user/{user_id}")
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                      current_user: Annotated[UserOut, Depends(get_current_user)]):
    is_user_admin(current_user)
    delete_user = db_manager.delete_user(user_id)
    if isinstance(delete_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=delete_user)
    return {'Success': f'User {delete_user} was deleted successfully.'}


@admins.put("/user/{user_id}")
async def update_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                      user: UserIn,
                      current_user: Annotated[UserOut, Depends(get_current_user)]) -> UserOut:
    is_user_admin(current_user)
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


@admins.patch("/user/{user_id}")
async def patch_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                     user: UserPatch,
                     current_user: Annotated[UserOut, Depends(get_current_user)]) -> UserOut:
    is_user_admin(current_user)
    db_user = db_manager.get_user_by_id(user_id)
    if isinstance(db_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user)
    stored_user_model = UserIn(**db_user.__dict__)
    update_data = user.model_dump(exclude_unset=True)
    updated_user = stored_user_model.model_copy(update=update_data)
    db_user_updated = await update_user(user_id, updated_user)
    return db_user_updated
