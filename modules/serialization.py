from data.database_manager import db_manager
from data.models import *
from data.schemas import *


def word_out_from_user_word(user_word: UsersWords) -> WordOut:
    word_out = WordOut(
        id=user_word.id,
        word=user_word.word.word,
        word_type=user_word.word.word_type.name,
        english=user_word.word.english,
        level=user_word.word.level,
        topic=user_word.topic.name,
        example=[user_word.word_example.example, user_word.word_example.translation]
    )
    if user_word.custom_translation:
        word_out.english = user_word.custom_translation
    return word_out


if __name__ == '__main__':
    word = db_manager.get_user_words(37)[1]
    print(word_out_from_user_word(word))