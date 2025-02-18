from fastapi import APIRouter, Depends, Path, Query
from typing import Annotated, Literal

from data.schemas import UserOut, WordOut, UserWordIn, UserWordPatch, TopicOut
from data.database_manager import db_manager
from modules.security import get_current_active_user
from modules.word_info import get_word_info_from_search, get_word_info, get_words_suggestion
import modules.serialization as serialization
from modules.utils import check_for_exception, raise_exception

words = APIRouter(prefix='/users/me/words', tags=['user_words'])
user_topics = APIRouter(prefix='/users/me/topics', tags=['user_topics'])


@words.get('', summary="Show user's words")
async def read_own_words(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        limit: Annotated[int, Query(title='words limit', description='words per request', ge=1, le=100)] = 25,
        skip: Annotated[int, Query(title='skip pages', description='pages to skip', ge=0)] = 0,
        sort_by: Literal['id', 'level', 'word', 'word_type', 'english', 'example'] = 'id',
        desc: Annotated[bool, Query(description='true - descending order')] = False
) -> list[WordOut]:
    """## Show user words info
    Available query parameters:
    - *limit* - amount of words to be shown
    - *skip* - how many pages with _limit_ to skip (0 - first page, 1 - second page etc.)
    - *sort_by* - word attribute for sorting
    - *desc* - should sorting be ascending (false) or descending (true)
    """
    db_users_words = db_manager.get_user_words(current_user.id, limit, skip, sort_by, desc)
    return serialization.word_out_list_from_user_words(db_users_words)


@words.get('/suggest', summary='Suggest words from letter combination')
async def suggest_words_by_letter_combination(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        letter_combination: Annotated[str, Query(title='Combination of letters', min_length=3)],
        page_start: Annotated[int, Query(title='Page number', description='Pagination parameter', ge=1, le=20)] = 1,
        pages: Annotated[int, Query(title='Amount of pages',
                                    description='Pagination parameter',
                                    ge=1, le=20)] = 1
) -> list[dict] | str:
    """## Given a letter combination shows a list of suggested words
    - *letter combination* - combination of letters that should be present in words
    - *page_start* - what page should suggestions start from
    - *pages* - amount of pages to show at once. More pages means longer response time
    """
    suggest_words = get_words_suggestion(letter_combination, page_start, pages)
    for word in suggest_words:
        del word['url']
    return suggest_words


@words.get('/{user_word_id}', summary="Show user word's info")
async def get_own_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        user_word_id: Annotated[int, Path(title='UserWord id', ge=1)]
) -> WordOut:
    """## Given a user_word_id returns the user word's info"""
    db_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_word, 404)
    if db_word.user_id != current_user.id:
        raise_exception(403, f'User "{current_user.username}" is allowed to see only his/her own words.')
    return serialization.word_out_from_user_word(db_word)


@words.post('', summary='Add a user word')
async def add_user_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        word: UserWordIn
) -> WordOut:
    """## Adds new word to user's words
    Word can be added:
    1. by providing only one german word (all info will be fetched automatically).
    2. by providing *word*, *translation*, *level* and *word_type*.

    """
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
    if db_manager.user_has_word(current_user.id, the_word, parsed_word['word_type']):
        raise_exception(409, f"User '{current_user.username}' already has word '{the_word}' "
                             f"({parsed_word['word_type']}).")
    db_word = db_manager.get_word_by_word(the_word, parsed_word['word_type'])
    if isinstance(db_word, str):
        db_user_word = db_manager.add_user_word(user_id=current_user.id,
                                                word=parsed_word,
                                                example=word.example,
                                                example_translation=word.example_translation,
                                                topics=word.topics,
                                                translation=word.english)
        if custom_word:
            db_manager.add_non_parsed_word_record(current_user.id, db_user_word.word.id)
        return serialization.word_out_from_user_word(db_user_word)
    db_user_word = db_manager.add_user_word(user_id=current_user.id,
                                            word=parsed_word,
                                            topics=word.topics,
                                            translation=word.english)
    return serialization.word_out_from_user_word(db_user_word)


@words.delete('/{user_word_id}', summary="Removes user's word from the app")
async def remove_user_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        user_word_id: Annotated[int, Path(ge=1)]
) -> WordOut | None:
    """## Given *user_word_id* removes it from the app
    This action is irreversible.
    """
    the_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(the_word, 404)
    if current_user.id != the_word.user_id:
        raise_exception(403, "User can remove only his/her own words.")
    serialized_word = serialization.word_out_from_user_word(the_word)
    db_manager.remove_user_word(user_word_id)
    return serialized_word


@words.patch('/{user_word_id}', summary="Update user word's info")
async def patch_own_word(user_word_id: Annotated[int, Path(ge=1)],
                         current_user: Annotated[UserOut, Depends(get_current_active_user)],
                         word: UserWordPatch) -> WordOut:
    """## Update info for user word with *user_word_id*
    Expected at least one of the parameters:
     - word
     - word_type
     - english
     - level
     - topics
     - example
     - example_translation
     """
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_user_word, 404)
    if db_user_word.user_id != current_user.id:
        raise_exception(403, "User can remove only his/her own words.")
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
    if isinstance(updated_db_user_word, str) and 'not found' in updated_db_user_word:
        raise_exception(404, updated_db_user_word)
    check_for_exception(updated_db_user_word, 409)
    return serialization.word_out_from_user_word(updated_db_user_word)


@words.put('/{user_word_id}', summary="Update user word's info")
async def update_own_word(user_word_id: Annotated[int, Path(ge=1)],
                          current_user: Annotated[UserOut, Depends(get_current_active_user)],
                          word: UserWordIn) -> WordOut:
    """## Update info for user word with *user_word_id*
    All parameters are required."""
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_user_word, 404)
    if db_user_word.user_id != current_user.id:
        raise_exception(403, "User can remove only his/her words.")
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


@user_topics.get('', summary="Shows all user's topics")
async def get_own_topics(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        limit: Annotated[int, Query(title='words limit', description='topics per request', ge=1, le=100)] = 25,
        skip: Annotated[int, Query(title='skip pages', description='pages to skip', ge=0)] = 0,
        sort_by: Literal['id', 'name'] = 'id',
        desc: Annotated[bool, Query(description='true - descending order')] = False
) -> list[TopicOut]:
    """## Get a list of all user's topics
    User topics can be ordered by topic's _name_ or _id_ in ascending or descending order."""
    user_topics_list = db_manager.get_user_topics(current_user.id, limit, skip, sort_by, desc)
    check_for_exception(user_topics_list, 404)
    return user_topics_list


@user_topics.get('/{topic_id}', summary="Show all user topic's words")
async def get_own_topic_words(
        topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        limit: Annotated[int, Query(title='words limit', description='words per request', ge=1, le=100)] = 25,
        skip: Annotated[int, Query(title='skip pages', description='pages to skip', ge=0)] = 0,
        sort_by: Literal['id', 'word', 'word_type', 'level', 'english', 'example'] = 'id',
        desc: Annotated[bool, Query(description='true - descending order')] = False
) -> list[WordOut]:
    """## Get a list of all words from user topic with *topic_id*
    Words can be sorted and paginated.
    """
    own_topic_words = db_manager.get_user_topic_words(current_user.id, topic_id, limit, skip, sort_by, desc)
    check_for_exception(own_topic_words, 404)
    return serialization.word_out_list_from_user_words(own_topic_words)


@user_topics.put('/{topic_id}', summary="Update topic's name")
async def update_own_topic_name(topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
                                current_user: Annotated[UserOut, Depends(get_current_active_user)],
                                topic_name: str) -> TopicOut:
    """## Update user's topic
    """
    updated_user_topic = db_manager.update_user_topic(current_user.id, topic_id, topic_name)
    check_for_exception(updated_user_topic, 404)
    return updated_user_topic


@user_topics.delete('/{topic_id}', summary='Delete topic from the app')
async def remove_own_topic(topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
                           current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> TopicOut:
    """## Delete topic from the application
    This action is **irreversible**. This will delete the topic and all related user words as well."""
    user_topic = db_manager.delete_user_topic(current_user.id, topic_id)
    check_for_exception(user_topic, 404)
    return user_topic
