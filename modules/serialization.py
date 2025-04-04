from data.database_manager import db_manager
from data.models import *
from data.schemas import *


def word_out_from_user_word(user_word: UserWord) -> WordOut:
    word_out = WordOut(
        id=user_word.id,
        word=user_word.word.word,
        word_type=user_word.word.word_type.name,
        english=user_word.word.english,
        level=user_word.word.level,
        topics=[word_topic.topic.name for word_topic in user_word.user_word_topic]
    )
    if user_word.word.example:
        word_out.example = user_word.word.example.example
        word_out.example_translation = user_word.word.example.translation
    if user_word.custom_translation:
        word_out.english = user_word.custom_translation.translation
    if user_word.example:
        word_out.example = user_word.example.example
        word_out.example_translation = user_word.example.translation
    return word_out


def word_out_list_from_user_words(user_words: list[UserWord]) -> list[WordOut]:
    return [word_out_from_user_word(user_word) for user_word in user_words]


def admin_word_from_word(db_word: Word) -> AdminWordOut:
    admin_word_out = AdminWordOut(
        id=db_word.id,
        word=db_word.word,
        word_type=db_word.word_type.name,
        english=db_word.english,
        level=db_word.level,
        users=db_manager.get_word_users(db_word.id)
    )
    if db_word.example:
        admin_word_out.example = db_word.example.example
        admin_word_out.example_translation = db_word.example.translation
    return admin_word_out


def admin_wordlist_from_words(words: list[Word]) -> list[AdminWordOut]:
    if not words:
        return []
    return [admin_word_from_word(admin_word) for admin_word in words]


def user_out_admin(user: User) -> UserOutAdmin:
    user.role = user.user_role.role.name
    return user


def admin_wordlist_out_from_user_words(words: list[UserWord], sort_by: str) -> list[AdminUserWordOut]:
    wordlist = []
    for user_word in words:
        admin_word = AdminUserWordOut(
            id=user_word.id,
            word_id=user_word.word_id,
            word=user_word.word.word,
            user_id=user_word.user_id,
            topics=[user_topic.topic.name for user_topic in user_word.user_word_topic],
            fails=user_word.fails,
            success=user_word.success,
            last_shown=user_word.last_shown,
            custom_translation=user_word.custom_translation,
            custom_level=user_word.user_level
        )
        if user_word.example:
            admin_word.custom_example = user_word.example.example
        wordlist.append(admin_word)
    return wordlist


def admin_word_out_from_db_word(db_word: Word) -> AdminWord:
    word_out = AdminWord(
        id=db_word.id,
        word=db_word.word,
        word_type=db_word.word_type.name,
        english=db_word.english,
        level=db_word.level,
        example=db_word.example.example,
        example_translation=db_word.example.translation
    )
    return word_out


def user_word_card_from_user_word(db_word: UserWord) -> UserWordCard:
    user_word_card = UserWordCard(
        id=db_word.id,
        word=db_word.word.word,
        word_type=db_word.word.word_type.name,
        level=db_word.word.level,
        english=db_word.word.english,
        example=db_word.word.example.example,
        example_translation=db_word.word.example.translation,
        topics=[user_topic.topic.name for user_topic in db_word.user_word_topic],
        fails=db_word.fails,
        success=db_word.success,
        last_shown=db_word.last_shown
    )
    if db_word.custom_translation:
        user_word_card.english = db_word.custom_translation.translation
    if db_word.user_level:
        user_word_card.level = db_word.user_level.level
    if db_word.example:
        user_word_card.example = db_word.example.example
        user_word_card.example_translation = db_word.example.translation
    return user_word_card


if __name__ == '__main__':
    # word = db_manager.get_user_words(6)[0]
    # print(word_out_from_user_word(word))
    u_words = word_out_list_from_user_words(db_manager.get_user_words(6), 'word_type')
    [print(u_wo) for u_wo in u_words]
