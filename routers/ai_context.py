from fastapi import APIRouter, Path, Query, Depends
from typing import Annotated, Literal

from data.database_manager import db_manager
from data.schemas import UserOut, ContextSentence
from modules.security import get_current_active_user
from modules.utils import check_for_exception, raise_exception
import modules.ai as ai

topic_context = APIRouter(prefix='/context/topic', tags=['topic_context'])


@topic_context.get('/{topic_id}')
async def generate_sentence_from_topic(
        current_user: Annotated[UserOut, Depends(get_current_active_user)],
        topic_id: Annotated[int, Path(ge=1)],
        words_count: Annotated[int, Literal[1, 2]],
        level: Literal['user_level', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2']) -> dict:
    db_topic_user_words = db_manager.get_random_user_words_from_topic(current_user.id, topic_id, words_count)
    if isinstance(db_topic_user_words, str) and 'has no words' in db_topic_user_words:
        raise_exception(403, db_topic_user_words)
    check_for_exception(db_topic_user_words, 404)
    prompt_words = [f'{user_word.word.word} ({user_word.word.word_type.name})' for user_word in db_topic_user_words]
    topic = db_manager.get_topic_by_id(topic_id).name
    prompt = ai.build_sentence_prompt(topic, level, prompt_words)
    ai_response = await ai.ai_request(prompt)
    check_for_exception(ai_response, 504)
    return ai_response if isinstance(ai_response, dict) \
        else raise_exception(504, 'AI needs to rest. Try again later.')
