import os
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, exc
from sqlalchemy.orm import sessionmaker
from data.models import Base, User, Word, UsersWords, UsersWordsTopics, Topic, WordType, WordExample


class DataManager:

    def __init__(self, database_url_object):
        self._engine = create_engine(url_object, echo=True)
        Base.metadata.create_all(self._engine)
        Session = sessionmaker(bind=self._engine)
        self.session = Session()

    def get_user_by_id(self, user_id: int):
        try:
            result = self.session.query(User).filter(User.id == user_id).one()
        except exc.NoResultFound:
            result = f'User with id={user_id} was not found.'
        return result

    def get_user_by_username(self):
        pass

    def get_user_by_email(self):
        pass

    def add_user(self):
        pass

    def delete_user(self):
        pass

    def update_user(self):
        pass


load_dotenv()
url_object = URL.create(
    # 'postgresql+pg8000',
    'postgresql+psycopg2',
    username=os.getenv('pg_username'),
    password=os.getenv('pg_password'),
    host=os.getenv('pg_host'),
    port=os.getenv('pg_port'),
    database=os.getenv('pg_database')
)

db_manager = DataManager(url_object)


def db_test():
    print(db_manager.get_user_by_id(18))


if __name__ == '__main__':
    db_test()
