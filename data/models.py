from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, TIMESTAMP, Sequence, Enum, UniqueConstraint
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
    level = Column(Enum('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='level'), default='A1')

    users_words = relationship("UserWord", back_populates="user", cascade="all, delete-orphan")
    non_parsed_word = relationship("NonParsedWord", back_populates="user")
    user_role = relationship("UserRole", back_populates="user", uselist=False, cascade="all, delete")

    def __str__(self):
        return f'{self.id}. {self.username} ({self.email} - {self.user_role.role.name})'

    def __repr__(self):
        return self.__str__()


class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, Sequence('roles_id_seq'), primary_key=True)
    name = Column(String, Enum('Admin', 'Manager', 'User', name='user_roles_enum'), unique=True)

    user_role = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = 'user_roles'

    id = Column(Integer, Sequence('user_roles_id_seq'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    user = relationship("User", back_populates="user_role")
    role = relationship("Role", back_populates="user_role")


class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, Sequence('word_id_seq'), primary_key=True)
    word = Column(String, nullable=False)
    word_type_id = Column(Integer, ForeignKey('word_types.id', ondelete='CASCADE'), nullable=False)
    english = Column(String, nullable=False)
    level = Column(String)
    __table_args__ = UniqueConstraint('word', 'word_type_id', name='_unique_word'),

    word_type = relationship("WordType", back_populates="words")
    users_word = relationship("UserWord", back_populates="word")
    example = relationship("WordExample", back_populates="word", uselist=False)
    non_parsed_word = relationship("NonParsedWord", back_populates="word", uselist=False)

    def __str__(self):
        return f'{self.id}. {self.word} ({self.level}) - {self.english}'

    def __repr__(self):
        return self.__str__()


class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, Sequence('topic_id_seq'), primary_key=True)
    name = Column(String, unique=True)

    users_words = relationship("UserWord", back_populates="topic")
    users_words_topics = relationship("UserWordTopic", cascade="all, delete", back_populates="topic")

    def __str__(self):
        return f'{self.id}. {self.name}'

    def __repr__(self):
        return self.__str__()


class WordType(Base):
    __tablename__ = 'word_types'

    id = Column(Integer, Sequence('word_type_id_seq'), primary_key=True)
    name = Column(String, unique=True, nullable=False)

    words = relationship("Word", cascade="all, delete-orphan", back_populates="word_type")

    def __str__(self):
        return f'{self.id}. {self.name}'

    def __repr__(self):
        return self.__str__()


class WordExample(Base):
    __tablename__ = 'words_examples'

    id = Column(Integer, Sequence('word_example_id_seq'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'), unique=True)
    example = Column(String, nullable=False)
    translation = Column(String)

    word = relationship("Word", back_populates="example")

    def __str__(self):
        return f'{self.id}. word={self.word.word}: {self.example} - {self.translation}'

    def __repr__(self):
        return self.__str__()


class UserWord(Base):
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
    users_words_topics = relationship("UserWordTopic", cascade="all, delete-orphan", back_populates="user_words")
    custom_translation = relationship("UserWordTranslation", back_populates="user_word",
                                      uselist=False, cascade="all, delete")
    example = relationship("UserWordExample", back_populates="user_word", uselist=False, cascade="all, delete")
    user_level = relationship("UserWordLevel", cascade="all, delete", back_populates="user_word")

    def __str__(self):
        return (f'{self.id}. user={self.user.username}, word={self.word.word}: '
                f'(fails={self.fails}, success={self.success}, last_shown={self.last_shown}')

    def __repr__(self):
        return self.__str__()


class UserWordTranslation(Base):
    __tablename__ = 'users_words_translations'

    id = Column(Integer, Sequence('users_words_translations_id_seq'), primary_key=True)
    user_word_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'), nullable=False)
    translation = Column(String, nullable=False)

    user_word = relationship("UserWord", back_populates="custom_translation")

    def __str__(self):
        return f'{self.id}. user={self.user_word.user.username}, word={self.user_word.word.word} - {self.translation}'

    def __repr__(self):
        return self.__str__()


class UserWordExample(Base):
    __tablename__ = 'users_words_examples'

    id = Column(Integer, Sequence('users_words_examples_id_seq'), primary_key=True)
    users_words_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'), unique=True)
    example = Column(String, nullable=False)
    translation = Column(String)

    user_word = relationship("UserWord", back_populates="example", uselist=False)

    def __str__(self):
        return f'{self.id}. word={self.user_word.word.word}: {self.example} ({self.translation})'

    def __repr__(self):
        return self.__str__()


class UserWordTopic(Base):
    __tablename__ = 'users_words_topics'

    id = Column(Integer, Sequence('users_words_topic_id_seq'), primary_key=True)
    user_words_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'))
    topic_id = Column(Integer, ForeignKey('topics.id', ondelete='CASCADE'))

    user_words = relationship("UserWord", back_populates="users_words_topics")
    topic = relationship("Topic", back_populates="users_words_topics")


class NonParsedWord(Base):
    __tablename__ = 'non_parsed_words'

    id = Column(Integer, Sequence('non_parsed_words_id_seq'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'), unique=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))

    word = relationship("Word", back_populates="non_parsed_word", cascade="all, delete")
    user = relationship("User", back_populates="non_parsed_word", cascade="all, delete")

    def __str__(self):
        return f'{self.id}. word {self.word.word} added by {self.user.username}'

    def __repr__(self):
        return self.__str__()


class UserWordLevel(Base):
    __tablename__ = 'users_words_levels'

    id = Column(Integer, Sequence('users_words_levels_id_seq'), primary_key=True)
    user_word_id = Column(Integer, ForeignKey('users_words.id', ondelete='CASCADE'), unique=True)
    level = Column(Enum('A1', 'A2', 'B1', 'B2', 'C1', 'C2', name='level'))

    user_word = relationship("UserWord", back_populates="user_level")

    def __str__(self):
        return (f'{self.id}. user={self.user_word.user.username}, word={self.user_word.word.word}, '
                f'custom_level={self.level}')

    def __repr__(self):
        return self.__str__()
