import os
import datetime
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, exc
from sqlalchemy.orm import sessionmaker

from data.models import Base, User, Word, UsersWords, UsersWordsTopics, Topic, WordType, WordExample


class DataManager:

    def __init__(self, database_url_object):
        self._engine = create_engine(database_url_object, echo=False)
        Base.metadata.create_all(self._engine)
        self.session = sessionmaker(bind=self._engine)()

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
            result = self.session.query(User).filter_by(username=username).one()
        except exc.NoResultFound:
            result = f'User with username "{username}" was not found.'
        return result

    def get_user_by_email(self, email):
        try:
            result = self.session.query(User).filter_by(email=email).one()
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
            delete_user = self.session.query(User).filter_by(id=user_id).one()
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

    def update_user(self, user_id: int, username: str, email: str, password: str, level: str) -> type[User] | str:
        user = self.get_user_by_id(user_id)
        if isinstance(user, str):
            return user
        user.username = username
        user.email = email
        user.password = password
        user.level = level
        self.session.commit()
        self.session.refresh(user)
        return user

    def add_word_type(self, word_type: str) -> WordType:
        try:
            db_word_type = self.session.query(WordType).filter_by(name=word_type).one()
        except exc.NoResultFound:
            db_word_type = WordType(name=word_type)
            self.session.add(db_word_type)
            self.session.commit()
            self.session.refresh(db_word_type)
        return db_word_type

    def get_word_type(self, word_type_id: int) -> WordType | str:
        try:
            db_word_type = self.session.query(WordType).filter_by(id=word_type_id).one()
        except exc.NoResultFound:
            db_word_type = f'Word type with id={word_type_id} was not found'
        return db_word_type

    def add_word_example_id(self, word_id: int, example: list[str]) -> id:
        try:
            db_example = self.session.query(WordExample).filter_by(example=example[0]).one()
        except exc.NoResultFound:
            db_example = WordExample(
                word_id=word_id,
                example=example[0],
                translation=example[1]
            )
            self.session.add(db_example)
            self.session.commit()
            self.session.refresh(db_example)
        return db_example.id

    def add_topic(self, topic: str, description: str | None = None) -> Topic:
        try:
            db_topic = self.session.query(Topic).filter_by(name=topic).one()
        except exc.NoResultFound:
            db_topic = Topic(
                name=topic,
                description=description
            )
            self.session.add(db_topic)
            self.session.commit()
            self.session.refresh(db_topic)
        return db_topic

    def get_topic_by_id(self, topic: str) -> Topic:
        pass

    def get_word_by_id(self, word_id: int) -> type[Word]:
        try:
            db_word = self.session.query(Word).filter_by(id=word_id).one()
        except exc.NoResultFound:
            db_word = f'Word with id={word_id} was not found.'
        return db_word

    def get_word_by_word(self, word: str) -> type(Word) | dict:
        try:
            db_word = self.session.query(Word).filter_by(word=word).one()
            return db_word
        except exc.NoResultFound:
            return {'error': 'No word "{word}" found.'}

    def get_user_word_by_id(self, user_word_id: int) -> UsersWords:
        pass

    def add_user_word(self,
                      user_id: int,
                      word: dict,
                      example: list | None = None,
                      topic: str | None = None,
                      topic_description: str | None = None,
                      translation: str | None = None) -> Word | str:
        db_word = self.add_new_word(word)
        # if isinstance(db_word, str):
        #     return db_word
        user_word = UsersWords(
            word_id=db_word.id,
            user_id=user_id,
            last_shown=datetime.datetime(1, 1, 1)
        )
        if not example and word.get('example'):
            db_example = self.add_word_example(db_word.id, word['example'][0], word['example'][1])
            user_word.example = db_example.id
        elif example:
            db_example = self.add_word_example(db_word.id, example[0], example[1])
            user_word.example = db_example.id
        if not topic:
            topic = 'Default'
        db_topic = self.add_topic(topic)
        user_word.topic_id = db_topic.id
        if translation:
            user_word.custom_translation = translation
        self.session.add(user_word)
        self.session.commit()
        self.session.refresh(user_word)
        return user_word

    def add_word_example(self, word_id: int, example: str, translation: str) -> WordExample:
        try:
            db_example = self.session.query(WordExample).filter_by(example=example).one()
        except exc.NoResultFound:
            db_example = WordExample(
                word_id=word_id,
                example=example,
                translation=translation
            )
            self.session.add(db_example)
            self.session.commit()
            self.session.refresh(db_example)
        return db_example

    def add_new_word(self, word: dict) -> Word:
        db_word = self.get_word_by_word(word['word'])
        if isinstance(db_word, Word):
            return db_word

        word_type = self.add_word_type(word['word_type'])
        new_word = Word(
            word=word['word'],
            word_type_id=word_type.id,
            level=word['level'],
            english=word['translation']
        )
        self.session.add(new_word)
        self.session.commit()
        self.session.refresh(new_word)
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
    print(db_manager.get_users())
