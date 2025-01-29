from fastapi import APIRouter, Depends, Path, Query
from typing import Annotated, Literal
from datetime import datetime

from data.schemas import UserOut, UserWordCard
from data.database_manager import db_manager
from modules.security import get_current_active_user
import modules.serialization as serialization
from modules.utils import check_for_exception, raise_exception

cards = APIRouter(prefix='/user_cards', dependencies=[Depends(get_current_active_user)], tags=['user_cards'])


@cards.get('/topic/{topic_id}')
async def get_topic_cards(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                          topic_id: Annotated[int | None, Path(ge=1)],
                          limit: Annotated[int, Query(ge=1, le=50)] = 25,
                          random: bool = False
                          ) -> list[UserWordCard]:
    db_cards = db_manager.get_user_cards(current_user.id, topic_id, limit, random)
    check_for_exception(db_cards, 404)
    return [serialization.user_word_card_from_user_word(user_word) for user_word in db_cards]


@cards.get('/random')
async def get_random_cards(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                           limit: Annotated[int, Query(ge=1, le=50)] = 25):
    random_db_words = db_manager.get_random_user_words(current_user.id, limit)
    check_for_exception(random_db_words, 404)
    return [serialization.user_word_card_from_user_word(user_word) for user_word in random_db_words]


@cards.get('/update_info/{user_word_id}')
async def update_card_info(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                           user_word_id: Annotated[int, Path(ge=1)],
                           guess: Literal['fails', 'success']) -> UserWordCard:
    db_user_word = db_manager.get_user_word_by_id(user_word_id)
    check_for_exception(db_user_word, 404)
    if db_user_word.user_id != current_user.id:
        raise_exception(403, f"User with id={current_user.id} "
                             f"doesn't have a user word with id={user_word_id}")
    updated_user_word = db_manager.update_card(user_word_id, datetime.now(), guess)
    return serialization.user_word_card_from_user_word(updated_user_word)
