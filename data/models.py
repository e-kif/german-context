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
    login_attempts = Column(Integer)
    last_activity = Column(DateTime)
    created_at = Column(TIMESTAMP, server_default=func.now())
    streak = Column(Integer)
    level = Column(String, default='A1')

    # Relationship with users_words
    users_words = relationship("UsersWords", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return f'{self.id}. {self.username} ({self.email})'

    def __repr__(self):
        return f'{self.id}. {self.username} ({self.email})'


class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, Sequence('word_id_seq'), primary_key=True)
    word = Column(String, unique=True, nullable=False)
    word_type_id = Column(Integer, ForeignKey('word_types.id', ondelete='CASCADE'), nullable=False)
    english = Column(String, nullable=False)
    level = Column(String, nullable=False)

    word_type = relationship("WordType", back_populates="words")
    users_word = relationship("UsersWords", back_populates="word")
    examples = relationship("WordExample", cascade="all, delete", back_populates="word")

    def __str__(self):
        return f'{self.id}. {self.word} ({self.level}) - {self.english}'

    def __repr__(self):
        return f'{self.id}. {self.word} ({self.level}) - {self.english}'


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, Sequence('topic_id_seq'), primary_key=True)
    name = Column(String, unique=True)

    users_words = relationship("UsersWords", back_populates="topic")
    users_words_topics = relationship("UsersWordsTopics", cascade="all, delete", back_populates="topic")

    def __str__(self):
        return f'{self.id}. {self.name}'

    def __repr__(self):
        return f'{self.id}. {self.name}'


class WordType(Base):
    __tablename__ = 'word_types'

    id = Column(Integer, Sequence('word_type_id_seq'), primary_key=True)
    name = Column(String, unique=True, nullable=False)
    questions = Column(String)

    words = relationship("Word", cascade="all, delete-orphan", back_populates="word_type")

    def __str__(self):
        return f'{self.id}. {self.name}'

    def __repr__(self):
        return f'{self.id}. {self.name}'


class WordExample(Base):
    __tablename__ = 'words_examples'

    id = Column(Integer, Sequence('word_example_id_seq'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'))
    example = Column(Text, unique=True)
    translation = Column(Text)

    word = relationship("Word", back_populates="examples")
    users_words = relationship("UsersWords", back_populates="word_example")

    def __str__(self):
        return f'{self.id}. word_id={self.word_id}: {self.example} - {self.translation}'

    def __repr__(self):
        return f'{self.id}. word_id={self.word_id}: {self.example} - {self.translation}'


class UsersWords(Base):
    __tablename__ = 'users_words'

    id = Column(Integer, Sequence('users_word_id_seq'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))
    fails = Column(Integer, default=0)
    success = Column(Integer, default=0)
    last_shown = Column(DateTime)

    word = relationship("Word", back_populates="users_word")
    user = relationship("User", back_populates="users_words")
    topic = relationship("Topic", back_populates="users_words")
    users_words_topics = relationship("UsersWordsTopics", cascade="all, delete-orphan", back_populates="user_words")
    word_example = relationship("WordExample", cascade="all, delete", back_populates="users_words")
    custom_translation = relationship("UsersWordsTranslations", back_populates="user_word")
    example = relationship("UsersWordsExamples", back_populates="user_word")

    def __str__(self):
        return (f'{self.id}. user={self.user.username}, word={self.word.word}: '
                f'(fails={self.fails}, success={self.success}, last_shown={self.last_shown}')

    def __repr__(self):
        return (f'{self.id}. user={self.user.username}, word={self.word.word}: '
                f'(fails={self.fails}, success={self.success}, last_shown={self.last_shown}')


class UsersWordsTranslations(Base):
    __tablename__ = 'users_words_translations'

    id = Column(Integer, Sequence('users_words_translations_id_seq'), primary_key=True)
    user_word_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'))
    translation = Column(String)

    user_word = relationship("UsersWords", back_populates="custom_translation")

    def __str__(self):
        return f'{self.id}. user={self.user_word.user.username}, word={self.user_word.word.word} - {self.translation}'

    def __repr__(self):
        return f'{self.id}. user={self.user_word.user.username}, word={self.user_word.word.word} - {self.translation}'


class UsersWordsExamples(Base):
    __tablename__ = 'users_words_examples'

    id = Column(Integer, Sequence('users_words_examples_id_seq'), primary_key=True)
    users_words_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'))
    example = Column(String, nullable=False)
    translation = Column(String)

    user_word = relationship("UsersWords", back_populates="example")

    def __str__(self):
        return f'{id}. word={self.user_word.word.word}: {self.example} ({self.translation})'


class UsersWordsTopics(Base):
    __tablename__ = 'users_words_topics'

    id = Column(Integer, Sequence('users_words_topic_id_seq'), primary_key=True)
    user_words_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'))
    topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))

    user_words = relationship("UsersWords", back_populates="users_words_topics")
    topic = relationship("Topic", back_populates="users_words_topics")
