from fastapi import FastAPI, Path, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Any

from data.database_manager import db_manager
from data.schemas import *
from modules.security import (Token,
                              authenticate_user,
                              ACCESS_TOKEN_EXPIRE_MINUTES,
                              get_current_active_user,
                              create_access_token,
                              get_password_hash)
from modules.word_info import get_word_info
import modules.serialization as serialization

app = FastAPI()


@app.get("/")
async def home():
    return {'message': 'home'}


@app.get("/users")
async def get_users() -> list[UserOut]:
    return db_manager.get_users()


@app.get("/user/{user_id}", response_model=UserOut)
async def get_user(user_id: Annotated[int, Path(ge=0, title='User ID')]) -> Any:
    user = db_manager.get_user_by_id(user_id)
    if isinstance(user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=user)
    return user


@app.post("/users")
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


@app.put("/user/{user_id}", response_model=UserOut)
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


@app.patch("/user/{user_id}", response_model=UserOut)
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


@app.delete("/user/{user_id}")
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)]):
    delete_user = db_manager.delete_user(user_id)
    if isinstance(delete_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=delete_user)
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


@app.get("/users/me/", response_model=UserOut)
async def read_users_me(
        current_user: Annotated[UserBase, Depends(get_current_active_user)],
):
    return current_user


@app.get("/users/me/words/")
async def read_own_words(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
) -> list[WordOut]:
    db_users_words = db_manager.get_user_words(current_user.id)
    users_words_out = []
    for user_word in db_users_words:
        users_words_out.append(serialization.word_out_from_user_word(user_word))
    return users_words_out


@app.post("/users/me/words")
async def add_user_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        word: WordIn
) -> WordOut:
    parsed_word = get_word_info(word.word)
    if isinstance(parsed_word, str) and not all([word.translation, word.level, word.word_type]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=parsed_word + " Provide following values: 'translation', 'level', 'word_type'.")
    elif isinstance(parsed_word, str):
        parsed_word = dict(
            word=word.word,
            translation=word.translation,
            level=word.level,
            word_type=word.word_type,
            topic=word.topic
        )
    the_word = parsed_word.get('word', word.word)
    if db_manager.user_has_word(current_user.id, the_word):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User '{current_user.username}' already has word '{the_word}'.")
    db_user_word = db_manager.add_user_word(user_id=current_user.id,
                                            word=parsed_word,
                                            example=word.example,
                                            topic=word.topic,
                                            translation=word.translation)
    return serialization.word_out_from_user_word(db_user_word)


@app.delete("/users/me/words/{user_word_id}")
async def remove_user_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        user_word_id: Annotated[int, Path(ge=1)]
) -> WordOut | None:
    the_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(the_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=the_word)
    if current_user.id != the_word.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User can remove only his words.")
    db_manager.remove_user_word(user_word_id)
    return serialization.word_out_from_user_word(the_word)


@app.patch("/users/me/words/{user_word_id}")
async def update_own_word(user_word_id: Annotated[int, Path(ge=1)],
                          current_user: Annotated[UserOut, Depends(get_current_active_user)],
                          word: WordPatch) -> WordOut:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(db_user_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user_word)
    if db_user_word.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User can update only his words.")
    stored_word_model = WordOut(**serialization.word_out_from_user_word(db_user_word).__dict__)
    update_data = word.model_dump(exclude_unset=True)
    updated_user_word = stored_word_model.model_copy(update=update_data)
    print(updated_user_word)
    # todo check translation update (users_words.custom_translation)
    # todo implement db update
    return updated_user_word
