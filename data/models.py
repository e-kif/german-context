import dotenv
import dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, registry

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, TIMESTAMP, Text, Sequence
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String)
    last_login = Column(DateTime)
    login_attempts = Column(Integer, nullable=False)
    last_activity = Column(DateTime)
    created_at = Column(TIMESTAMP, server_default=func.now())
    streak = Column(Integer)
    level = Column(String, default='A1')

    # Relationship with users_words
    users_words = relationship("UsersWords", back_populates="user")

    def __str__(self):
        return f'{self.id}. {self.username} ({self.email})'


class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, Sequence('word_id_seq'), primary_key=True)
    word = Column(String)
    word_type_id = Column(Integer, ForeignKey('word_types.id'))
    english = Column(String)
    level = Column(String)

    # Relationship with word_type
    word_type = relationship("WordType", back_populates="words")

    # Relationship with users_words
    users_words = relationship("UsersWords", back_populates="word")

    # Relationship with word_examples
    examples = relationship("WordExample", back_populates="word")


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, Sequence('topic_id_seq'), primary_key=True)
    name = Column(String)
    description = Column(String)

    # Relationships with users_words and users_words_topics
    users_words = relationship("UsersWords", back_populates="topic")
    users_words_topics = relationship("UsersWordsTopics", back_populates="topic")


class WordType(Base):
    __tablename__ = 'word_types'

    id = Column(Integer, Sequence('word_type_id_seq'), primary_key=True)
    name = Column(String)
    questions = Column(String)

    # Relationship with words
    words = relationship("Word", back_populates="word_type")


class WordExample(Base):
    __tablename__ = 'words_examples'

    id = Column(Integer, Sequence('word_example_id_seq'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'))
    example = Column(Text)
    translation = Column(Text)

    # Relationship with word
    word = relationship("Word", back_populates="examples")


class UsersWords(Base):
    __tablename__ = 'users_words'

    id = Column(Integer, Sequence('users_word_id_seq'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    custom_translation = Column(String, default=None)
    example = Column(Integer, ForeignKey('words_examples.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))
    fails = Column(Integer)
    success = Column(Integer)
    last_shown = Column(DateTime)

    # Relationships with word, user, topic, and example
    word = relationship("Word", back_populates="users_words")
    user = relationship("User", back_populates="users_words")
    topic = relationship("Topic", back_populates="users_words")
    word_example = relationship("WordExample")

    users_words_topics = relationship("UsersWordsTopics", back_populates="user_words")


class UsersWordsTopics(Base):
    __tablename__ = 'users_words_topics'

    id = Column(Integer, Sequence('users_words_topic_id_seq'), primary_key=True)
    user_words_id = Column(Integer, ForeignKey('users_words.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))

    # Relationships with users_words and topic
    user_words = relationship("UsersWords", back_populates="users_words_topics")
    topic = relationship("Topic", back_populates="users_words_topics")




dotenv_path = '.env'
url_object = URL.create(
    # 'postgresql+pg8000',
    'postgresql+psycopg2',
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
