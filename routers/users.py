from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated

from data.schemas import UserIn, UserOut, UserPatch, UserBase
from data.database_manager import db_manager
from modules.security import get_password_hash, get_current_active_user

users = APIRouter(tags=['users'])


@users.get("/users")
async def get_users() -> list[UserOut]:
    return db_manager.get_users()


@users.post("/users")
async def add_user(user: UserIn) -> UserBase:
    new_user = db_manager.add_user(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    if isinstance(new_user, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=new_user)
    return new_user


@users.put("/user/me", response_model=UserOut)
async def update_user(user: UserIn,
                      current_user: Annotated[UserOut, Depends(get_current_active_user)]):
    updated_user = db_manager.update_user(
        user_id=current_user.id,
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    if isinstance(updated_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=updated_user)
    return updated_user


@users.patch("/user/me", response_model=UserOut)
async def patch_user(user: UserPatch,
                     current_user: Annotated[UserOut, Depends(get_current_active_user)]):
    db_user = db_manager.get_user_by_id(current_user.id)
    if isinstance(db_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user)
    stored_user_model = UserIn(**db_user.__dict__)
    update_data = user.model_dump(exclude_unset=True)
    updated_user = stored_user_model.model_copy(update=update_data)
    db_user_updated = await update_user(updated_user, current_user)
    return db_user_updated


@users.get("/users/me/", response_model=UserOut)
async def read_users_me(
        current_user: Annotated[UserBase, Depends(get_current_active_user)],
):
    return current_user


@users.delete("/users/me/")
async def remove_self(current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> UserOut:
    db_user = db_manager.get_user_by_id(current_user.id)
    if isinstance(db_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'User with id={current_user.id} was not found.')
    deleted_user = db_manager.delete_user(db_user.id)
    return deleted_user
