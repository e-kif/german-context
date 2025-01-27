import os
import datetime
from typing import Type

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, exc, text, desc
from sqlalchemy.orm import sessionmaker

from data.models import *
from modules.word_info import get_word_info_from_search


class DataManager:

    def __init__(self, database_url_object):
        self._engine = create_engine(database_url_object, echo=False)
        Base.metadata.create_all(self._engine)
        self.session = sessionmaker(bind=self._engine)()

    def get_users(self, limit: int = 25, skip: int = 0):
        return self.session.query(User).order_by(User.id).slice(limit * skip, limit * (skip + 1)).all()

    def get_user_by_id(self, user_id: int):
        try:
            result = self.session.query(User).filter_by(id=user_id).one()
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
            self.session.execute(text("SELECT SETVAL('user_id_seq', (SELECT COALESCE(MAX(id)) FROM users), true)"))
            return error.args[0].split('\n')[1].split(':')[1].strip()
        if len(self.get_users()) == 1:
            self.assign_user_role(new_user.id, 'Admin')
        else:
            self.assign_user_role(new_user.id, 'User')
        self.session.commit()
        return new_user

    def add_role(self, role: str):
        try:
            db_role = self.session.query(Role).filter_by(name=role).one()
        except exc.NoResultFound:
            db_role = Role(name=role)
            self.session.add(db_role)
            self.session.commit()
            self.session.refresh(db_role)
        return db_role

    def change_user_role(self, user_id: int, role: str):
        db_user = self.get_user_by_id(user_id)
        if isinstance(db_user, str):
            return db_user
        db_role = self.add_role(role)
        db_user.user_role.role_id = db_role.id
        self.session.commit()
        return db_user

    def assign_user_role(self, user_id: int, role: str):
        db_user = self.get_user_by_id(user_id)
        if isinstance(db_user, str):
            return db_user
        db_role = self.add_role(role)
        db_user_role = UserRole(user_id=db_user.id,
                                role_id=db_role.id)
        self.session.add(db_user_role)
        self.session.commit()
        self.session.refresh(db_user_role)
        return db_user_role

    def check_user_role(self, user_id: int, role: str):
        db_user = self.get_user_by_id(user_id)
        if isinstance(db_user, str):
            return db_user
        return db_user.user_role.role.name == role

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

    def update_user(self, user_id: int, username: str, email: str, password: str, level: str) -> Type[User] | str:
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

    def add_topic(self, topic: str) -> Topic:
        try:
            db_topic = self.session.query(Topic).filter_by(name=topic).one()
        except exc.NoResultFound:
            db_topic = Topic(name=topic)
            self.session.add(db_topic)
            self.session.commit()
            self.session.refresh(db_topic)
        return db_topic

    def get_topic_by_topic(self, topic: str) -> str | Type[Topic]:
        try:
            db_topic = self.session.query(Topic).filter_by(name=topic).one()
        except exc.NoResultFound:
            return f'Topic named "{topic}" was not found.'
        return db_topic

    def get_topic_by_id(self, topic_id: int) -> str | Type[Topic]:
        try:
            db_topic = self.session.query(Topic).filter_by(id=topic_id).one()
        except exc.NoResultFound:
            return f'Topic with id={topic_id} was not found.'
        return db_topic

    def get_words(self, limit: int = 25, skip: int = 0) -> list[Type[Word]]:
        db_words = self.session.query(Word).order_by(Word.id).slice(limit * skip, limit * (skip + 1)).all()
        return db_words

    def get_word_users(self, word_id: int) -> list[int]:
        word_users = {user_word.user_id for user_word in self.session.query(UserWord)
                      .filter_by(word_id=word_id).order_by(UserWord.user_id).all()}
        return list(word_users)

    def get_word_by_id(self, word_id: int) -> Type[Word]:
        try:
            db_word = self.session.query(Word).filter_by(id=word_id).one()
        except exc.NoResultFound:
            db_word = f'Word with id={word_id} was not found.'
        return db_word

    def delete_word(self, word_id: int) -> str | Type[Word]:
        db_word = self.get_word_by_id(word_id)
        if isinstance(db_word, str):
            return db_word
        self.session.delete(db_word)
        self.session.commit()
        return db_word

    def update_word(self,
                    word_id,
                    word: str,
                    word_type: str,
                    english: str,
                    level: str,
                    example: str | None = None,
                    example_translation: str | None = None) -> str | Type[Word]:
        db_word = self.get_word_by_id(word_id)
        if isinstance(db_word, str):
            return db_word
        db_word.word = word
        db_word.word_type_id = self.add_word_type(word_type).id
        db_word.english = english
        db_word.level = level
        if example:
            db_word.example.example = example
            db_word.example.translation = example_translation
        self.session.commit()
        self.session.refresh(db_word)
        return db_word

    def get_word_by_word(self, word: str, word_type: str) -> Type[Word] | str:
        try:
            db_word = (self.session.query(Word).join(WordType)
                       .filter(Word.word == word, WordType.name == word_type).one())
            return db_word
        except exc.NoResultFound:
            return f'No word "{word}" found.'

    def get_user_word_by_id(self, user_word_id: int) -> UserWord | str:
        try:
            db_user_word = self.session.query(UserWord).filter_by(id=user_word_id).one()
        except exc.NoResultFound:
            db_user_word = f'User word with id={user_word_id} was not found.'
        return db_user_word

    def get_user_words(self, user_id: int, limit: int = 25, skip: int = 0) -> str | list[Type[UserWord]]:
        db_user = db_manager.get_user_by_id(user_id)
        if isinstance(db_user, str):
            return db_user
        db_users_words = self.session.query(UserWord).filter_by(user_id=user_id).order_by(UserWord.id) \
            .slice(skip * limit, (skip + 1) * limit).all()
        return db_users_words

    def add_user_word(self,
                      user_id: int,
                      word: dict,
                      example: str | None = None,
                      example_translation: str | None = None,
                      topics: list[str] | None = None,
                      translation: str | None = None) -> Word | str:
        db_word = self.add_new_word(word)
        user_word = UserWord(
            word_id=db_word.id,
            user_id=user_id,
            last_shown=datetime.datetime(1, 1, 1)
        )
        self.session.add(user_word)
        self.session.commit()
        self.session.refresh(user_word)
        if not topics:
            topics = ['Default']
        for topic in topics:
            db_topic = self.add_topic(topic)
            self.add_user_word_topic(user_word.id, db_topic.id)
        if not example and word.get('example'):
            self.add_word_example(db_word.id, word['example'][0], word['example'][1])
        elif example:
            self.add_user_word_example(user_word.id, example, example_translation)
        if translation:
            self.add_user_word_translation(user_word.id, translation)
        return user_word

    def add_user_word_topic(self, user_word_id: int, topic_id: int) -> UserWordTopic:
        user_word_topic = UserWordTopic(user_word_id=user_word_id,
                                        topic_id=topic_id)
        try:
            self.session.add(user_word_topic)
            self.session.commit()
            self.session.refresh(user_word_topic)
        except exc.IntegrityError:
            self.session.rollback()
            user_word_topic = self.session.query(UserWordTopic).filter_by(user_word_id=user_word_id) \
                .filter_by(topic_id=topic_id).one()
        return user_word_topic

    def add_word_example(self, word_id: int, example: str, translation: str) -> WordExample:
        try:
            db_example = self.session.query(WordExample).filter_by(word_id=word_id).one()
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

    def add_user_word_example(self, user_word_id: int, example: str, translation: str | None) -> UserWordExample:
        user_word_example = UserWordExample(
            user_word_id=user_word_id,
            example=example,
            translation=translation
        )
        self.session.add(user_word_example)
        self.session.commit()
        self.session.refresh(user_word_example)
        return user_word_example

    def add_user_word_translation(self, user_word_id: int, translation: str) -> UserWordTranslation | str:
        try:
            db_user_word = self.session.query(UserWord).filter_by(id=user_word_id).one()
        except exc.NoResultFound:
            return f'User word with id={user_word_id} was not found'
        if db_user_word.custom_translation:
            db_user_word.custom_translation.translation = translation
            self.session.commit()
            return db_user_word.custom_translation
        user_word_translation = UserWordTranslation(
            user_word_id=user_word_id,
            translation=translation
        )
        self.session.add(user_word_translation)
        self.session.commit()
        self.session.refresh(user_word_translation)
        return user_word_translation

    def user_has_word(self, user_id: int, word: str, word_type: str):
        db_word = self.get_word_by_word(word, word_type)
        if isinstance(db_word, str):
            return False
        try:
            self.session.query(UserWord).filter_by(user_id=user_id, word_id=db_word.id).one()
            return True
        except exc.NoResultFound:
            return False

    def get_user_word_by_word(self, user_id: int, word: str) -> str | Type[UserWord]:
        pass

    def user_word_has_translation(self, user_word_id: int) -> bool:
        try:
            db_user_word = self.session.query(UserWord).filter_by(id=user_word_id).one()
        except exc.NoResultFound:
            return False
        return bool(db_user_word.custom_translation)

    def add_user_word_level(self, user_word_id: int, level: str) -> UserWordLevel | str:
        db_user_word = self.get_user_word_by_id(user_word_id)
        if isinstance(db_user_word, str):
            return f'User word with id={user_word_id} was not found.'
        if db_user_word.user_level:
            db_user_word.user_level.level = level
        else:
            user_level = UserWordLevel(
                user_word_id=user_word_id,
                level=level
            )
            self.session.add(user_level)
        self.session.commit()
        return db_user_word.user_level

    def update_user_word(self,
                         user_word_id: int,
                         word: str = None,
                         word_type: str = None,
                         english: str = None,
                         level: str = None,
                         topics: list[str] = None,
                         example: str = None,
                         example_translation: str = None) -> UserWord | str:
        db_user_word = self.get_user_word_by_id(user_word_id)
        if isinstance(db_user_word, str):
            return db_user_word
        if db_user_word.word.non_parsed_word:
            db_user_word.word.word = word
            db_user_word.word.english = english
            db_user_word.word.level = level
            db_user_word.word.word_type = self.add_word_type(word_type).id
        elif db_user_word.word.word_type.name != word_type or db_user_word.word.word != word:
            db_word = self.get_word_by_word(word, word_type)
            if isinstance(db_word, Word):  # user adds a word that is present in db
                old_word = self.session.query(Word).filter_by(id=db_user_word.word_id).one()
                db_user_word.word_id = db_word.id
                try:
                    self.session.query(UserWord).filter_by(word_id=old_word.id) \
                        .filter(UserWord.user_id.op('!=')(db_user_word.user_id)).first()
                except exc.NoResultFound:
                    self.session.delete(old_word)
                if english != db_word.english and not db_user_word.custom_translation:
                    user_translation = UserWordTranslation(
                        user_word_id=user_word_id,
                        translation=english
                    )
                    self.session.add(user_translation)
                else:
                    db_user_word.custom_translation.translation = english
                if level != db_word.level:
                    self.add_user_word_level(db_user_word.id, level)
            else:  # the word is not in db
                new_word = get_word_info_from_search(word, word_type)  # user adds new word
                if isinstance(new_word, dict):  # user adds parsed word
                    db_new_word = self.add_new_word(new_word)
                    db_user_word.word_id = db_new_word.id
        else:
            if level != db_user_word.word.level:
                self.add_user_word_level(db_user_word.id, level)
            if english != db_user_word.word.english:
                self.add_user_word_translation(db_user_word.id, english)
            if not db_user_word.example:
                self.add_user_word_example(db_user_word.id, example, example_translation)
            if example != db_user_word.example.example or example_translation != db_user_word.example.translation:
                db_user_word.example.example = example
                db_user_word.example.translation = example_translation
        print(f'{topics=}')
        for topic in topics:
            print(f'{topic=}')
            self.add_user_word_topic(db_user_word.id, self.add_topic(topic).id)
        self.session.commit()
        self.session.refresh(db_user_word)
        return db_user_word

    def add_new_word(self, word: dict) -> Word:
        db_word = self.get_word_by_word(word['word'], word['word_type'])
        if isinstance(db_word, Word) and db_word.word_type.name == word.get('word_type'):
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

    def add_non_parsed_word_record(self, user_id: int, word_id: int):
        non_parsed_word_record = NonParsedWord(
            user_id=user_id,
            word_id=word_id
        )
        self.session.add(non_parsed_word_record)
        self.session.commit()
        self.session.refresh(non_parsed_word_record)
        return non_parsed_word_record

    def remove_user_word(self, user_word_id) -> UserWord | str:
        try:
            db_user_word = self.session.query(UserWord).filter_by(id=user_word_id).one()
            self.session.delete(db_user_word)
            self.session.commit()
        except exc.NoResultFound:
            db_user_word = f'No user word with id={user_word_id} was found.'
        return db_user_word

    def get_user_topics(self, user_id: int, limit: int = 25, skip: int = 0, sort_by: str = 'id', reverse: int = 0
                        ) -> str | list[Type[Topic]]:
        try:
            self.session.query(User).filter_by(id=user_id).one()
        except exc.NoResultFound:
            return f'User with user_id={user_id} was not found.'
        sorting = self.sort_order(Topic, sort_by, reverse)
        user_topics = self.session.query(Topic).join(UserWordTopic).join(UserWord).join(User) \
            .filter_by(id=user_id).order_by(sorting).slice(limit * skip, limit * (skip + 1)).all()
        return user_topics

    @staticmethod
    def sort_order(model, sort_by: str, reverse: int = 0):
        sorting = model.__dict__.get(sort_by)
        return desc(sorting) if reverse else sorting

    def get_user_topic_words(self,
                             user_id: int,
                             topic_id: int,
                             limit: int = 25,
                             skip: int = 0) -> str | list[Type[UserWord]]:
        try:
            self.session.query(User).filter_by(id=user_id).one()
        except exc.NoResultFound:
            return f'User with user_id={user_id} was not found.'
        try:
            self.session.query(Topic).filter_by(id=topic_id).one()
        except exc.NoResultFound:
            return f'Topic with topic_id={topic_id} was not found.'
        user_topic_words = self.session.query(UserWord).filter_by(user_id=user_id).join(UserWordTopic) \
            .filter_by(topic_id=topic_id).order_by(UserWord.id).slice(limit * skip, limit * (skip+1)).all()
        if not user_topic_words:
            return f'User with id={user_id} has no words in topic with id={topic_id}.'
        return user_topic_words

    def delete_user_topic(self, user_id: int, topic_id: int) -> str | Type[Topic]:
        try:
            user_topic = self.session.query(Topic).filter_by(id=topic_id).join(UserWordTopic) \
                .join(UserWord).filter_by(user_id=user_id).one()
        except exc.NoResultFound:
            return f'User topic for user_id={user_id} and topic_id={topic_id} was not found.'
        other_user_uses_topic = bool(self.session.query(Topic).filter_by(id=topic_id).join(UserWordTopic)
                                     .join(UserWord).filter(UserWord.user_id != user_id).first())
        if not other_user_uses_topic:
            self.session.delete(user_topic)
            self.session.commit()
            return user_topic
        user_topic_words = self.session.query(UserWordTopic).filter_by(topic_id=topic_id) \
            .join(UserWord).filter_by(user_id=user_id).all()
        self.session.delete(user_topic_words)
        self.session.commit()
        return user_topic

    def update_user_topic(self, user_id: int, topic_id: int, topic_name: str) -> str | Type[Topic]:
        user_topic_word = self.session.query(UserWordTopic).filter_by(topic_id=topic_id) \
            .join(UserWord).filter_by(user_id=user_id).first()
        if not user_topic_word:
            return f'User with user_id={user_id} has no words in topic with topic_id={topic_id}.'
        other_user_uses_topic = bool(self.session.query(Topic).filter_by(id=topic_id).join(UserWordTopic)
                                     .join(UserWord).filter(UserWord.user_id != user_id).first())
        if other_user_uses_topic:
            db_topic = self.add_topic(topic_name)
            for user_word in self.get_user_topic_words(user_id, topic_id, 100000):
                user_word.user_word_topic[0].topic_id = db_topic.id
            self.session.commit()
            return db_topic
        db_topic = self.session.query(Topic).filter_by(id=topic_id).one()
        db_topic.name = topic_name
        self.session.commit()
        self.session.refresh(db_topic)
        return db_topic


load_dotenv()
url_object = URL.create(
    drivername=os.getenv('db_drivername'),
    username=os.getenv('db_username'),
    password=os.getenv('db_password'),
    host=os.getenv('db_host'),
    port=os.getenv('db_port'),
    database=os.getenv('db_database')
)

db_manager = DataManager(url_object)

if __name__ == '__main__':
    # db_manager.session.rollback()
    # print(db_manager.check_user_role(1, 'User'))
    print(db_manager.get_users())
