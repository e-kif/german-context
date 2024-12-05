from dotenv import get_key
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from models import User, UsersWords, UsersWordsTopics, Topic, WordExample, Base

dotenv_path = '.env'
url_object = URL.create(
    'postgresql+psycopg2',
    username=get_key(dotenv_path, 'pg_username'),
    password=get_key(dotenv_path, 'pg_password'),
    host=get_key(dotenv_path, 'pg_host'),
    port=get_key(dotenv_path, 'pg_port'),
    database=get_key(dotenv_path, 'pg_database'),
)


class DataManager():
    pass


engine = create_engine(url_object, echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
