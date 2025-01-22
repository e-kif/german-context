from fastapi import APIRouter, Path, Query, Depends
from typing import Annotated

from data.schemas import (UserOutAdmin, UserIn, UserPatchAdmin, UserInAdmin,
                          WordOut, WordIn, UserWordIn, UserWordPatch, WordPatch, AdminWordOut,
                          TopicOut, AdminUserWordOut,
                          AdminWord)
from data.database_manager import db_manager
from modules.security import get_password_hash, is_user_admin, get_current_user
import modules.serialization as serialization
from modules.word_info import get_word_info, get_word_info_from_search, get_words_suggestion
from modules.utils import check_for_exception, raise_exception

admin_users = APIRouter(prefix='/admin/users', dependencies=[Depends(is_user_admin)], tags=['admin_users'])
admin_words = APIRouter(prefix='/admin/words', dependencies=[Depends(is_user_admin)], tags=['admin_words'])
admin_user_words = APIRouter(prefix='/admin/user_words', dependencies=[Depends(is_user_admin)],
                             tags=['admin_user_words'])
admin_user_topics = APIRouter(prefix='/admin/user_topics', dependencies=[Depends(is_user_admin)],
                              tags=['admin_user_topics'])
admin_topics = APIRouter(prefix='/admin_topics', dependencies=[Depends(is_user_admin)], tags=['admin_topics'])


@admin_users.get('')
async def get_users() -> list[UserOutAdmin]:
    users = db_manager.get_users()
    users_out = [serialization.user_out_admin(user) for user in users]
    return users_out


@admin_users.post('/add')
async def add_user(user: UserInAdmin) -> UserOutAdmin:
    new_user = db_manager.add_user(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    check_for_exception(new_user, 409)
    db_manager.assign_user_role(new_user.id, user.role)
    return new_user


@admin_users.get('/me')
async def read_admin_me(admin: Annotated[UserOutAdmin, Depends(get_current_user)]) -> UserOutAdmin:
    return serialization.user_out_admin(admin)


@admin_users.get('/{user_id}')
async def get_user(user_id: Annotated[int, Path(ge=1, title='User ID')]) -> UserOutAdmin:
    user = db_manager.get_user_by_id(user_id)
    check_for_exception(user, 404)
    return serialization.user_out_admin(user)


@admin_users.delete('/{user_id}')
async def remove_user(user_id: Annotated[int, Path(title='User ID', ge=1)]) -> UserOutAdmin:
    delete_user = db_manager.delete_user(user_id)
    check_for_exception(delete_user, 404)
    return serialization.user_out_admin(delete_user)


@admin_users.put('/{user_id}')
async def update_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                      user: UserInAdmin) -> UserOutAdmin:
    updated_user = db_manager.update_user(
        user_id=user_id,
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password),
        level=user.level
    )
    check_for_exception(updated_user, 404)
    return serialization.user_out_admin(updated_user)


@admin_users.patch('/{user_id}')
async def patch_user(user_id: Annotated[int, Path(title='User ID', ge=1)],
                     user: UserPatchAdmin) -> UserOutAdmin:
    db_user = db_manager.get_user_by_id(user_id)
    check_for_exception(db_user, 404)
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
    check_for_exception(db_word, 404, f'No user word with id={user_word_id} was found.')
    return serialization.word_out_from_user_word(db_word)


@admin_user_words.post('/{user_id}')
async def add_user_word(user_id: Annotated[int, Path(title='User ID', ge=1)],
                        word: UserWordIn) -> WordOut:
    db_user = db_manager.get_user_by_id(user_id)
    check_for_exception(db_user, 404)
    parsed_word = get_word_info(word.word)
    custom_word = False
    if isinstance(parsed_word, str) and not all([word.english, word.level, word.word_type]):
        searched_words = get_word_info_from_search(word.word)
        if isinstance(searched_words, list) and searched_words:
            suggestions = '; '.join([f"{searched_word['word']} ({searched_word['word_type']})"
                                     for searched_word in searched_words])
            raise_exception(404, f'Word "{word.word}" was not found. Try one of these: ' + suggestions)
        raise_exception(400, parsed_word + " Provide following values: 'translation', 'level', 'word_type'.")
    elif isinstance(parsed_word, str):
        parsed_word = dict(
            word=word.word,
            translation=word.english,
            level=word.level,
            word_type=word.word_type,
            topics=word.topics,
            example=word.example,
            example_translation=word.example_translation
        )
        custom_word = True
    the_word = parsed_word['word']
    if db_manager.user_has_word(db_user.id, the_word, parsed_word['word_type']):
        raise_exception(409, f"User '{db_user.username}' already has word '{the_word}' "
                             f"({parsed_word['word_type']}).")
    db_word = db_manager.get_word_by_word(the_word, parsed_word['word_type'])
    if isinstance(db_word, str):
        db_user_word = db_manager.add_user_word(user_id=db_user.id,
                                                word=parsed_word,
                                                example=word.example,
                                                example_translation=word.example_translation,
                                                topics=word.topics,
                                                translation=word.english)
        if custom_word:
            db_manager.add_non_parsed_word_record(db_user.id, db_user_word.word.id)
        return serialization.word_out_from_user_word(db_user_word)
    db_user_word = db_manager.add_user_word(user_id=db_user.id,
                                            word=parsed_word,
                                            topics=word.topics,
                                            translation=word.english)
    return serialization.word_out_from_user_word(db_user_word)


@admin_user_words.delete('/words/{user_word_id}')
async def remove_user_word(
        user_word_id: Annotated[int, Path(ge=1)]
) -> WordOut | None:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_user_word, 404)
    serialized_word = serialization.word_out_from_user_word(db_user_word)
    db_manager.remove_user_word(user_word_id)
    return serialized_word


@admin_user_words.patch('/words/{user_word_id}')
async def patch_own_word(user_word_id: Annotated[int, Path(ge=1)],
                         word: UserWordPatch) -> WordOut:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_user_word, 404)
    stored_word_model = WordOut(**serialization.word_out_from_user_word(db_user_word).__dict__)
    update_data = word.model_dump(exclude_unset=True)
    updated_user_word = stored_word_model.model_copy(update=update_data)
    updated_db_user_word = db_manager.update_user_word(
        user_word_id=user_word_id,
        word=updated_user_word.word,
        word_type=updated_user_word.word_type,
        english=updated_user_word.english,
        level=updated_user_word.level,
        topics=updated_user_word.topics,
        example=updated_user_word.example,
        example_translation=updated_user_word.example_translation
    )
    check_for_exception(updated_db_user_word, 404)
    return serialization.word_out_from_user_word(updated_db_user_word)


@admin_user_words.put('/words/{user_word_id}')
async def update_own_word(user_word_id: Annotated[int, Path(ge=1)],
                          word: UserWordIn) -> WordOut:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_user_word, 404)
    updated_db_user_word = db_manager.update_user_word(
        user_word_id=user_word_id,
        word=word.word,
        word_type=word.word_type,
        english=word.english,
        level=word.level,
        topics=word.topics,
        example=word.example,
        example_translation=word.example_translation
    )
    return serialization.word_out_from_user_word(updated_db_user_word)


@admin_words.get('')
async def get_words(limit: Annotated[int | None, Query(ge=0, title="Pagination Limit")] = None,
                    skip: Annotated[int, Query(ge=0, title='Pagination page offset')] = 0) -> list[AdminWordOut]:
    words = db_manager.get_words(limit=limit, skip=skip)
    return serialization.admin_wordlist_from_words(words)


@admin_words.get('/suggest')
async def suggest_word_by_letter_combination(
        letter_combination: Annotated[str, Query(min_length=3)],
        page_start: Annotated[int, Query(title='Page number', description='Pagination parameter', ge=1, le=20)] = 1,
        pages: Annotated[int, Query(title='Amount of pages',
                                    description='Pagination parameter. The bigger the number, the longer the wait.',
                                    ge=1, le=20)] = 1
) -> list[dict] | str:
    return get_words_suggestion(letter_combination, page_start, pages)


@admin_words.get('/{word_id}')
async def get_word(word_id: Annotated[int, Path(title='Word ID', ge=1)]) -> AdminWordOut:
    db_word = db_manager.get_word_by_id(word_id)
    check_for_exception(db_word, 404)
    return serialization.admin_word_from_word(db_word)


@admin_words.post('')
async def add_word(word: WordIn) -> AdminWord:
    db_word = db_manager.get_word_by_word(word.word, word.word_type)
    if not isinstance(db_word, str):
        raise_exception(409, f'Word {db_word.word} ({db_word.word_type} already exists.')
    parsed_word = get_word_info(word.word)
    if isinstance(parsed_word, str) and all([word.word_type, word.english, word.level]):
        db_word = db_manager.add_new_word(word)
        return serialization.admin_word_out_from_db_word(db_word)
    check_for_exception(parsed_word, 404)
    db_word = db_manager.add_new_word(parsed_word)
    if parsed_word.get('example'):
        db_manager.add_word_example(db_word.id, parsed_word['example'][0], parsed_word['example'][1])
    return serialization.admin_word_out_from_db_word(db_word)


@admin_words.delete('/{word_id}')
async def delete_word(word_id: Annotated[int, Path(title='Word ID', ge=1)]) -> AdminWord:
    db_word = db_manager.get_word_by_id(word_id)
    check_for_exception(db_word, 404)
    word_out = serialization.admin_word_out_from_db_word(db_word)
    db_manager.delete_word(word_id)
    return word_out


@admin_words.put('/{word_id}')
async def update_word(word_id: Annotated[int, Path(title='Word ID', ge=1)],
                      word: WordIn) -> AdminWordOut:
    db_word = db_manager.get_word_by_id(word_id)
    check_for_exception(db_word, 404)
    updated_word = db_manager.update_word(
        word=word.word,
        word_type=word.word_type,
        english=word.english,
        level=word.level,
        example=word.example,
        example_translation=word.example_translation
    )
    return serialization.admin_word_out_from_db_word(updated_word)


@admin_words.patch('/{user_word_id}')
async def patch_word(word_id: Annotated[int, Path(ge=1)],
                     word: WordPatch) -> AdminWordOut:
    db_word = db_manager.get_word_by_id(word_id)
    check_for_exception(db_word, 404)
    stored_word_model = WordOut(**serialization.word_out_from_user_word(db_word).__dict__)
    update_data = word.model_dump(exclude_unset=True)
    updated_word = stored_word_model.model_copy(update=update_data)
    updated_db_word = db_manager.update_word(
        user_word_id=word_id,
        word=updated_word.word,
        word_type=updated_word.word_type,
        english=updated_word.english,
        level=updated_word.level,
        topics=updated_word.topics,
        example=updated_word.example,
        example_translation=updated_word.example_translation
    )
    check_for_exception(updated_db_word, 404)
    return serialization.word_out_from_user_word(updated_db_word)


@admin_user_topics.get('/{user_id}')
async def get_user_topics(user_id: Annotated[int, Path(title='User ID', ge=1)]) -> list[TopicOut]:
    db_user = db_manager.get_user_by_id(user_id)
    check_for_exception(db_user, 404)
    user_topics = db_manager.get_user_topics(user_id)
    check_for_exception(user_topics, 404)
    return user_topics


@admin_user_topics.get('/{user_id}/{topic_id}/words')
async def get_user_topic_words(user_id: Annotated[int, Path(title='User ID', ge=1)],
                               topic_id: Annotated[int, Path(title='Topic ID', ge=1)]) -> list[AdminUserWordOut]:
    user_topic_words = db_manager.get_user_topic_words(user_id, topic_id)
    check_for_exception(user_topic_words, 404)
    return serialization.admin_wordlist_out_from_user_words(user_topic_words)


@admin_user_topics.put('/{user_id}/{topic_id}')
async def update_user_topic(user_id: Annotated[int, Path(title='User ID', ge=1)],
                            topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
                            topic_name: str) -> TopicOut:
    user_topic = db_manager.update_user_topic(user_id, topic_id, topic_name)
    check_for_exception(user_topic, 404)
    return user_topic


@admin_user_topics.delete('/{user_id}/{topic_id}')
async def remove_user_topic(user_id: Annotated[int, Path(title='User ID', ge=1)],
                            topic_id: Annotated[int, Path(title='Topic ID', ge=1)]) -> TopicOut:
    user_topic = db_manager.delete_user_topic(user_id, topic_id)
    check_for_exception(user_topic, 404)
    return user_topic
