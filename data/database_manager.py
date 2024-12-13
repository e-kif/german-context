import os
import datetime
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, exc
from sqlalchemy.orm import sessionmaker

from data.models import Base, User, Word, UsersWords, UsersWordsTopics, Topic, WordType, WordExample


class DataManager:

    def __init__(self, database_url_object):
        self._engine = create_engine(database_url_object, echo=False)
        Base.metadata.create_all(self._engine)
        Session = sessionmaker(bind=self._engine)
        self.session = Session()

    def get_users(self):
        return self.session.query(User).all()

    def get_user_by_id(self, user_id: int):
        try:
            result = self.session.query(User).filter(User.id == user_id).one()
        except exc.NoResultFound:
            result = f'User with id={user_id} was not found.'
        return result

    def get_user_by_username(self, username):
        try:
            result = self.session.query(User).filter(User.username == username).one()
        except exc.NoResultFound:
            result = f'User with username "{username}" was not found.'
        return result

    def get_user_by_email(self, email):
        try:
            result = self.session.query(User).filter(User.email == email).one()
        except exc.NoResultFound:
            result = f'User with E-Mail "{email}" was not found.'
        return result

    def add_user(self, username, email, password, level='A1'):
        new_user = User(username=username,
                        email=email,
                        created_at=datetime.datetime.now(),
                        streak=0,
                        level=level,
                        password=password,
                        login_attempts=0)
        try:
            self.session.add(new_user)
            self.session.commit()
            self.session.refresh(new_user)
        except exc.IntegrityError as error:
            self.session.rollback()
            return error.args[0].split('\n')[1].split(':')[1].strip()
        return new_user

    def delete_user(self, user_id):
        try:
            delete_user = self.session.query(User).filter(User.id == user_id).one()
        except exc.NoResultFound:
            return f'User with id={user_id} was not found.'
        self.session.delete(delete_user)
        self.session.commit()
        return delete_user

    def update_user_last_login(self, user_id: int):
        user = self.get_user_by_id(user_id)
        if not isinstance(user, str):
            user.last_login = datetime.datetime.now()
            user.login_attempts = 0
            user.last_activity = user.last_login
            self.session.commit()

    def add_user_login_attempts(self, user_id: int):
        user = self.get_user_by_id(user_id)
        if not isinstance(user, str):
            user.login_attempts += 1
            self.session.commit()

    def update_user(self, user_id: int, username: str, email: str, password: str, level: str):
        user = self.get_user_by_id(user_id)
        if isinstance(user, str):
            return user
        user.username = username
        user.email = email
        user.password = password
        user.level = level
        self.session.commit()
        return user

    def get_word_type_id(self, word_type: str) -> int:
        try:
            word_type_db = self.session.query(WordType).filter_by(name=word_type).one()
        except exc.NoResultFound:
            word_type_db = WordType(word_type=word_type)
            self.session.add(word_type_db)
            self.session.commit()
            self.session.refresh(word_type_db)
        return word_type_db.id

    def add_new_word(self, user_id: int, word: dict) -> Word | str:
        example = {'word': 'das Mädchen',
                   'level': 'A1',
                   'word_type': 'Noun',
                   'translation': 'girl, maid, girlfriend, lassie',
                   'example': ['Alle Mädchen lachten.', 'All the girls were laughing.']}
        word_type_id = self.get_word_type_id(word['word_type'])
        new_word = Word(
            word=word['word'],
            word_type_id=word_type_id,
            level=word['level'],
            english=word['translation']
        )
        try:
            self.session.add(new_word)
            self.session.commit()
            self.session.refresh(new_word)
        except exc.IntegrityError as error:
            self.session.rollback()
            new_word = self.session.query(Word).filter_by(word=word['word']).one()

        example = WordExample(
            word_id=new_word.id,
            example=word.get('example')[0],
            translation=word.get('example')[1]
        )
        return new_word


load_dotenv()
url_object = URL.create(
    drivername='postgresql+psycopg2',
    username=os.getenv('pg_username'),
    password=os.getenv('pg_password'),
    host=os.getenv('pg_host'),
    port=os.getenv('pg_port'),
    database=os.getenv('pg_database')
)

db_manager = DataManager(url_object)


if __name__ == '__main__':
    db_manager.update_user_last_login(34)
