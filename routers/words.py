from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated

from data.schemas import UserOut, WordOut, WordIn, WordPatch
from data.database_manager import db_manager
from modules.security import get_current_active_user
from modules.word_info import get_word_info
import modules.serialization as serialization


words = APIRouter(tags=['words'])


@words.get("/users/me/words/")
async def read_own_words(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
) -> list[WordOut]:
    db_users_words = db_manager.get_user_words(current_user.id)
    users_words_out = []
    for user_word in db_users_words:
        users_words_out.append(serialization.word_out_from_user_word(user_word))
    return users_words_out


@words.post("/users/me/words")
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
            topic=word.topic,
            example=word.example,
            example_translation=word.example_translation
        )
    the_word = parsed_word.get('word', word.word)
    if db_manager.user_has_word(current_user.id, the_word):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User '{current_user.username}' already has word '{the_word}'.")
    db_user_word = db_manager.add_user_word(user_id=current_user.id,
                                            word=parsed_word,
                                            example=word.example,
                                            example_translation=word.example_translation,
                                            topic=word.topic,
                                            translation=word.translation)
    return serialization.word_out_from_user_word(db_user_word)


@words.delete("/users/me/words/{user_word_id}")
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


@words.patch("/users/me/words/{user_word_id}")
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
