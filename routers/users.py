from fastapi import APIRouter, Path, HTTPException, status, Depends
from typing import Annotated, Any

from data.schemas import UserIn, UserOut, UserPatch, UserBase
from data.database_manager import  db_manager
from modules.security import get_password_hash, get_current_active_user

users = APIRouter(tags=['users'])


@users.get("/users")
async def get_users() -> list[UserOut]:
    return db_manager.get_users()


@users.get("/user/{user_id}", response_model=UserOut)
async def get_user(user_id: Annotated[int, Path(ge=0, title='User ID')]) -> Any:
    user = db_manager.get_user_by_id(user_id)
    if isinstance(user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=user)
    return user


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


@users.put("/user/{user_id}", response_model=UserOut)
async def update_user(user_id: Annotated[int, Path(title='User ID', ge=1)], user: UserIn):
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


@users.patch("/user/{user_id}", response_model=UserOut)
async def patch_user(user_id: Annotated[int, Path(title='User ID', ge=1)], user: UserPatch):
    db_user = db_manager.get_user_by_id(user_id)
    if isinstance(db_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user)
    stored_user_model = UserIn(**db_user.__dict__)
    update_data = user.model_dump(exclude_unset=True)
    updated_user = stored_user_model.model_copy(update=update_data)
    db_user_updated = await update_user(user_id, updated_user)
    return db_user_updated


@users.delete("/user/{user_id}")
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)]):
    delete_user = db_manager.delete_user(user_id)
    if isinstance(delete_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=delete_user)
    return {'Success': f'User {delete_user} was deleted successfully.'}


@users.get("/users/me/", response_model=UserOut)
async def read_users_me(
        current_user: Annotated[UserBase, Depends(get_current_active_user)],
):
    return current_user
