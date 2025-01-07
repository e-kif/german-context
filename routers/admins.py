from fastapi import APIRouter, Path, HTTPException, status, Depends
from typing import Annotated

from data.schemas import UserOut, UserIn, UserPatch, UserInRole, WordOut, WordIn, WordPatch, AdminWordOut
from data.database_manager import db_manager
from modules.security import get_current_user, get_password_hash
import modules.serialization as serialization
from modules.word_info import get_word_info, get_word_info_from_search


def is_user_admin(current_user: Annotated[UserOut, Depends(get_current_user)]) -> bool:
    if not db_manager.check_user_role(current_user.id, 'Admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'User "{current_user.username}" is not an Admin. Not enough privileges.')
    return True


admin_users = APIRouter(prefix='/admin/users', dependencies=[Depends(is_user_admin)], tags=['admin_users'])
admin_words = APIRouter(prefix='/admin/words', dependencies=[Depends(is_user_admin)], tags=['admin_words'])
admin_user_words = APIRouter(prefix='/admin/user_words', dependencies=[Depends(is_user_admin)],
                             tags=['admin_user_words'])


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


@admin_user_words.get('/{user_id}')
async def get_user_words(user_id: Annotated[int, Path(title='User ID', ge=1)]) -> list[WordOut]:
    user_words = db_manager.get_user_words(user_id)
    return serialization.word_out_list_from_user_words(user_words)


@admin_user_words.get('/words/{user_word_id}')
async def get_user_word(
        user_word_id: Annotated[int, Path(title='UserWord ID', ge=1)]
) -> WordOut:
    db_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(db_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user word with id={user_word_id} was found.')
    return serialization.word_out_from_user_word(db_word)


@admin_user_words.post('/{user_id}')
async def add_user_word(user_id: Annotated[int, Path(title='User ID', ge=1)],
                        word: WordIn) -> WordOut:
    db_user = db_manager.get_user_by_id(user_id)
    if isinstance(db_user, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user)
    parsed_word = get_word_info(word.word)
    custom_word = False
    if isinstance(parsed_word, str) and not all([word.english, word.level, word.word_type]):
        searched_words = get_word_info_from_search(word.word)
        if isinstance(searched_words, list) and searched_words:
            suggestions = '; '.join([f"{searched_word['word']} ({searched_word['word_type']})"
                                     for searched_word in searched_words])
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Word "{word.word}" was not found. Try one of these: ' + suggestions)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=parsed_word + " Provide following values: 'translation', 'level', 'word_type'.")
    elif isinstance(parsed_word, str):
        parsed_word = dict(
            word=word.word,
            translation=word.english,
            level=word.level,
            word_type=word.word_type,
            topic=word.topic,
            example=word.example,
            example_translation=word.example_translation
        )
        custom_word = True
    the_word = parsed_word['word']
    if db_manager.user_has_word(db_user.id, the_word, parsed_word['word_type']):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User '{db_user.username}' already has word '{the_word}' "
                                   f"({parsed_word['word_type']}).")
    db_word = db_manager.get_word_by_word(the_word, parsed_word['word_type'])
    if isinstance(db_word, str):
        db_user_word = db_manager.add_user_word(user_id=db_user.id,
                                                word=parsed_word,
                                                example=word.example,
                                                example_translation=word.example_translation,
                                                topic=word.topic,
                                                translation=word.english)
        if custom_word:
            db_manager.add_non_parsed_word_record(db_user.id, db_user_word.word.id)
        return serialization.word_out_from_user_word(db_user_word)
    db_user_word = db_manager.add_user_word(user_id=db_user.id,
                                            word=parsed_word,
                                            topic=word.topic,
                                            translation=word.english)
    return serialization.word_out_from_user_word(db_user_word)


@admin_user_words.delete('/words/{user_word_id}')
async def remove_user_word(
        user_word_id: Annotated[int, Path(ge=1)]
) -> WordOut | None:
    the_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(the_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=the_word)
    serialized_word = serialization.word_out_from_user_word(the_word)
    db_manager.remove_user_word(user_word_id)
    return serialized_word


@admin_user_words.patch('/words/{user_word_id}')
async def patch_own_word(user_word_id: Annotated[int, Path(ge=1)],
                         word: WordPatch) -> WordOut:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(db_user_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user_word)
    stored_word_model = WordOut(**serialization.word_out_from_user_word(db_user_word).__dict__)
    update_data = word.model_dump(exclude_unset=True)
    updated_user_word = stored_word_model.model_copy(update=update_data)
    updated_db_user_word = db_manager.update_user_word(
        user_word_id=user_word_id,
        word=updated_user_word.word,
        word_type=updated_user_word.word_type,
        english=updated_user_word.english,
        level=updated_user_word.level,
        topic=updated_user_word.topic,
        example=updated_user_word.example,
        example_translation=updated_user_word.example_translation
    )
    if isinstance(updated_db_user_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user_word)
    return serialization.word_out_from_user_word(updated_db_user_word)


@admin_user_words.put('/words/{user_word_id}')
async def update_own_word(user_word_id: Annotated[int, Path(ge=1)],
                          word: WordIn) -> WordOut:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(db_user_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user_word)
    updated_db_user_word = db_manager.update_user_word(
        user_word_id=user_word_id,
        word=word.word,
        word_type=word.word_type,
        english=word.english,
        level=word.level,
        topic=word.topic,
        example=word.example,
        example_translation=word.example_translation
    )
    return serialization.word_out_from_user_word(updated_db_user_word)


@admin_words.get('')
async def get_words() -> list[AdminWordOut]:
    words = db_manager.get_words()
    return serialization.admin_wordlist_from_words(words)
