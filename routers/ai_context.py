from fastapi import APIRouter, Path, Query, Depends
from typing import Annotated

from data.database_manager import db_manager
from modules.security import get_current_active_user
from modules.utils import check_for_exception, raise_exception

topic_context = APIRouter(prefix='/context/topic/', tags=['topic_context'])
