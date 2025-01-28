from fastapi import APIRouter, Depends, Path, Query
from typing import Annotated, Literal
from datetime import datetime

from data.schemas import WordOut, TopicOut, UserOut
from data.database_manager import db_manager
from modules.security import get_current_active_user
import modules.serialization as serialization
from modules.utils import check_for_exception, raise_exception

cards = APIRouter(prefix='/user_cards', dependencies=[Depends(get_current_active_user)], tags=['user_cards'])


@cards.get('/topic/{topic_id}')
async def get_topic_cards(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                          topic_id: Annotated[int, Path(ge=1)],
                          limit: Annotated[int, Query(ge=1, le=50)] = 25,
                          random: bool = False
                          ):
    pass


@cards.get('/random')
async def get_random_cards(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                           limit: Annotated[int, Query(ge=1, le=50)] = 25):
    pass


@cards.get('/update_info/{user_word_id}')
async def update_card_info(current_user: Annotated[UserOut, Depends(get_current_active_user)],
                           user_word_id: Annotated[int, Path(ge=1)],
                           guess: Literal['fails', 'success']):
    pass
