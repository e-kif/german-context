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
        topic=user_word.topic.name
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


if __name__ == '__main__':
    word = db_manager.get_user_words(1)[0]
    print(word_out_from_user_word(word))
