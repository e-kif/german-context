from datetime import datetime
from data.models import (Role, UserRole, User, Word, UserWord, Topic,
                         WordType, WordExample, UserWordTranslation)


def test_role():
    admin = Role(id=1, name='Admin')
    user = Role(id=1, name='User')
    assert admin.__repr__() == 'Role: 1. Admin'


def test_user_role():
    user_role = UserRole(id=1, user_id=1, role_id=1)
    assert user_role.id == 1
    assert user_role.user_id == 1
    assert user_role.role_id == 1


def test_user():
    tester = User(
        id=1,
        username='user_name',
        email='test@mail.com',
        level='A1',
    )
    role_model = Role(id=1, name='User')
    tester_role = UserRole(id=1, user_id=1, role_id=1)
    tester_role.role = role_model
    tester.user_role = tester_role
    assert tester.__repr__() == '1. user_name (test@mail.com - User)'


def test_word():
    table = Word(id=1, word='der Tisch', english='Table', level='A1')
    assert table.__repr__() == '1. der Tisch (A1) - Table'


def test_topic():
    topic = Topic(id=1, name='House')
    assert topic.__repr__() == '1. House'


def test_word_type():
    word_type = WordType(id=1, name='Noun')
    assert word_type.__repr__() == '1. Noun'


def test_word_example():
    word_example = WordExample(
        id=1, word_id=2, example='auf dem Tisch', translation='on the table')
    table = Word(id=2, word='der Tisch', english='Table', level='A1')
    word_example.word = table
    assert word_example.__repr__() == '1. word=der Tisch: auf dem Tisch - on the table'


def test_user_word():
    tester = User(id=1, username='tester', level='A1')
    table = Word(id=1, word='der Tisch', english='Table', level='A1')
    user_table = UserWord(id=1, user_id=1, word_id=1, fails=7,
                          success=4, last_shown=datetime.now(),
                          user=tester, word=table)
    assert user_table.__repr__() == f'1. user=tester, word=der Tisch: (fails=7, success=4, last_shown={
        user_table.last_shown})'


def test_user_word_translation():
    custom_translation = UserWordTranslation(
        id=7, user_word_id=12, translation='Vehicle')
    car = Word(id=8, word='das Auto', english='Car', level='A1')
    driver = User(id=2, username='driver', level='A1')
    drivers_car = UserWord(id=12, word_id=8, user_id=2, user=driver, word=car)
    custom_translation.user_word = drivers_car
    assert custom_translation.__repr__() == '7. user=driver, word=das Auto - Vehicle'
