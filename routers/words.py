from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated

from data.schemas import UserOut, WordOut, WordIn, WordPatch, TopicOut
from data.database_manager import db_manager
from modules.security import get_current_active_user
from modules.word_info import get_word_info_from_search, get_word_info
import modules.serialization as serialization

words = APIRouter(prefix='/users/me/words', tags=['user_words'])
user_topics = APIRouter(prefix='/users/me/topics', tags=['user_topics'])


@words.get('')
async def read_own_words(
        current_user: Annotated[UserOut, Depends(get_current_active_user)]
) -> list[WordOut]:
    db_users_words = db_manager.get_user_words(current_user.id)
    return serialization.word_out_list_from_user_words(db_users_words)


@words.get('/{user_word_id}')
async def get_own_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        user_word_id: Annotated[int, Path(title='UserWord id', ge=1)]
) -> WordOut:
    db_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(db_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user word with id={user_word_id} was found.')
    if db_word.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'User "{current_user.username}" is allowed to see only his/her own words.')
    return serialization.word_out_from_user_word(db_word)


@words.post('')
async def add_user_word(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        word: WordIn
) -> WordOut:
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
            topics=word.topics,
            example=word.example,
            example_translation=word.example_translation
        )
        custom_word = True
    the_word = parsed_word['word']
    if db_manager.user_has_word(current_user.id, the_word, parsed_word['word_type']):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User '{current_user.username}' already has word '{the_word}' "
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


@words.delete('/{user_word_id}')
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
    serialized_word = serialization.word_out_from_user_word(the_word)
    db_manager.remove_user_word(user_word_id)
    return serialized_word


@words.patch('/{user_word_id}')
async def patch_own_word(user_word_id: Annotated[int, Path(ge=1)],
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
    if isinstance(updated_db_user_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user_word)
    return serialization.word_out_from_user_word(updated_db_user_word)


@words.put('/{user_word_id}')
async def update_own_word(user_word_id: Annotated[int, Path(ge=1)],
                          current_user: Annotated[UserOut, Depends(get_current_active_user)],
                          word: WordIn) -> WordOut:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    if isinstance(db_user_word, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=db_user_word)
    if db_user_word.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User can update only his/her words.")
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


@user_topics.get('')
async def get_own_topics(current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> list[TopicOut]:
    user_topics_list = db_manager.get_user_topics(current_user.id)
    if isinstance(user_topics_list, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=user_topics_list)
    return user_topics_list


@user_topics.get('/{topic_id}')
async def get_own_topic_words(topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
                        current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> list[WordOut]:
    own_topic_words = db_manager.get_user_topic_words(current_user.id, topic_id)
    if isinstance(own_topic_words, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=own_topic_words)
    return serialization.word_out_list_from_user_words(own_topic_words)


@user_topics.put('/{topic_id}')
async def update_own_topic_name(topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
                          current_user: Annotated[UserOut, Depends(get_current_active_user)],
                          topic_name: str) -> TopicOut:
    updated_user_topic = db_manager.update_user_topic(current_user.id, topic_id, topic_name)
    if isinstance(updated_user_topic, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=updated_user_topic)
    return updated_user_topic


@user_topics.delete('/{topic_id}')
async def remove_own_topic(topic_id: Annotated[int, Path(title='Topic ID', ge=1)],
                     current_user: Annotated[UserOut, Depends(get_current_active_user)]) -> TopicOut:
    user_topic = db_manager.delete_user_topic(current_user.id, topic_id)
    if isinstance(user_topic, str):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=user_topic)
    return user_topic
