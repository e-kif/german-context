import dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from data.models import Base, User, Word, UsersWords, UsersWordsTopics, Topic, WordType, WordExample

dotenv_path = '.env'
url_object = URL.create(
    'postgresql',
    # 'postgresql+psycopg2',
    username=dotenv.get_key(dotenv_path, 'pg_username'),
    password=dotenv.get_key(dotenv_path, 'pg_password'),
    host=dotenv.get_key(dotenv_path, 'pg_host'),
    port=dotenv.get_key(dotenv_path, 'pg_port'),
    database=dotenv.get_key(dotenv_path, 'pg_database'),
)

engine = create_engine(url_object, echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


class DataManager:

    def __init__(self):
        pass

    def add_user(self):
        pass