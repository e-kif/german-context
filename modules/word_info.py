import requests
from bs4 import BeautifulSoup
from random import randint
from typing import Literal


def get_soup_for_word(word: str) -> BeautifulSoup | str:
    base_url = 'https://www.woerter.net/?w='
    try:
        response = requests.get(base_url + word.replace(' ', '+'))
    except requests.exceptions.ConnectionError:
        return f'Connection problem. Try again later.'
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup


def get_wordlist_from_word_search(
        word: str,
        word_type: Literal[
            'Noun', 'Verb', 'Adjective',
            'Pronoun', 'Preposition', 'Conjunction',
            'Adverb', 'Article', 'Particle'
        ] | None = None
) -> list[dict] | dict | str:
    base_url = 'https://woerter.net'
    search_url = base_url + '/search/?w='
    try:
        response = requests.get(search_url + word.replace(' ', '+'))
    except requests.exceptions.ConnectionError:
        return 'Connection problem. Try again later.'
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        word_cards = soup.find_all('div', attrs={'class': 'bTrf rClear'})
        words = []
        for current_word in word_cards:
            the_word = current_word.find('a').parent.find_all('span')[0].text
            info = current_word.find('p', attrs={'class': 'rInf rKln r1Zeile rU3px rO0px'})
            if not info.find('span'):
                words.append(dict(
                    word=the_word,
                    word_type=None,
                    level=None,
                    href=base_url + current_word.find('a')['href']
                ))
                continue
            level = None
            if 'bZrt' in str(info):
                level = info.find('span', attrs={'class': 'bZrt'}).text.strip()
                current_word_type = info.find_all('span')[1].text
            else:
                current_word_type = info.find_all('span')[0].text
            href = base_url + current_word.find('a')['href']
            words.append(dict(
                word=the_word,
                word_type=current_word_type,
                level=level,
                href=href
            ))
        if word_type:
            try:
                words = [word for word in words if word['word_type'].lower() == word_type.lower()][0]
            except IndexError:
                return f'Word "{word}" ({word_type}) was not found.'
        return words


def get_soup_from_url(url: str) -> BeautifulSoup:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup


def parse_word(soup: BeautifulSoup):
    word = soup.find('div', attrs={'class': 'rCntr rClear'})
    if word:
        if '\n' in word.text.strip():
            parts_new = word.text.replace('\n', '').split(',')
            if len(parts_new) == 2:
                return ' '.join(parts_new[::-1])
            the_word = parts_new[0]
            article = ", ".join([art.strip() for art in parts_new if art.strip()[0] == art.strip()[0].lower()])
            return f'{article} {the_word}'
        return word.text.strip()


def get_word_from_soup(soup: BeautifulSoup) -> tuple[str, BeautifulSoup | None]:
    word = parse_word(soup)
    if not word:
        url_object = soup.find('a', attrs={'class': 'rKnpf rNoSelect rKnUnt rKnObn'})
        if not url_object:
            return soup.find('i').text.strip(), None
        new_url = url_object.attrs['href']
        if 'http' not in new_url:
            new_url = 'https://woerter.net' + new_url
        soup = get_soup_from_url(new_url)
        word = parse_word(soup)
        return word, soup
    return word, soup


def get_word_level_and_type(soup: BeautifulSoup) -> tuple[str, str] | tuple[None, None]:
    card = soup.find('section', attrs={'class': 'rBox rBoxWht'})
    if not card:
        return None, None
    info = card.find('p', attrs={'class': 'rInf'}).find('span')
    if info:
        level = card.find('p', attrs={'class': 'rInf'}).find('span').text.strip()
        try:
            word_type = card.find('p', attrs={'class': 'rInf'}).find_all('span')[1].text.strip().capitalize()
        except IndexError:
            word_type = 'Verb'
        return level, word_type
    info = card.find('span', attrs={'class': 'rInf'}).find_all('span')
    level = info[0].text.strip()
    word_type = info[1].text.strip().capitalize()
    return level, word_type


def get_word_translation(soup: BeautifulSoup) -> str | None:
    div = soup.find('dd', attrs={'lang': 'en'})
    if not div:
        return None
    translation = div.find_all('span')[1].text.strip()
    return translation


def get_word_example(soup: BeautifulSoup) -> list[str]:
    cards_titles = soup.find_all('h2')
    examples = []
    for title in cards_titles:
        if 'example' in title.text.lower():
            examples = title.parent.parent.find('ul', attrs={'class': 'rLst rLstGt'})
    if not examples:
        return []
    examples = examples.find_all('li')
    for _ in range(10):
        example = examples[randint(0, len(examples) - 1)]
        example1 = example.text.split('\xa0')[0].strip().replace('\n', ' ')
        example2 = example.text.split('\xa0')[-1].strip().replace('\n', ' ')
        if example2:
            break
    try:
        return [example1, example2]
    except NameError:
        return []


def get_word_info(word: str) -> dict | str:
    soup = get_soup_for_word(word)
    if isinstance(soup, str):
        return soup
    word, soup = get_word_from_soup(soup)
    if not soup:
        return word
    word_info = {'word': word}
    level, word_type = get_word_level_and_type(soup)
    translation = get_word_translation(soup)
    example = get_word_example(soup)
    if level and word_type:
        word_info.update({'level': level, 'word_type': word_type})
        if word_info['level'].upper() not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            word_info['level'] = 'Unknown'
    if translation:
        word_info.update({'translation': translation})
    if example:
        word_info.update({'example': example})
    return word_info


def get_word_info_from_search(
        word: str,
        word_type: Literal[
            'Noun', 'Verb', 'Adjective',
            'Pronoun', 'Preposition', 'Conjunction',
            'Adverb', 'Article', 'Particle'
        ] | None = None
) -> dict | str | list:
    found_words = get_wordlist_from_word_search(word, word_type)
    if isinstance(found_words, str | list):
        return found_words
    soup = get_soup_from_url(found_words['href'])
    word_info = {'word': get_word_from_soup(soup)[0]}
    level, word_type_parsed = get_word_level_and_type(soup)
    translation = get_word_translation(soup)
    example = get_word_example(soup)
    if level and word_type:
        word_info.update({'level': level, 'word_type': word_type_parsed})
    if translation:
        word_info.update({'translation': translation})
    if example:
        word_info.update({'example': example})
    return word_info


def get_words_suggestion(letters: str, page_start: int = 1, pages: int = 1):
    base_url = 'https://www.woerter.net'
    base_search_url = base_url + '/search'
    search_url = base_search_url + '?w='

    response_text = ''
    for page_number in range(pages):
        try:
            response = requests.get(f'{search_url}{letters}&p={page_start + page_number}')
        except requests.exceptions.ConnectionError:
            print(f'Connection problem for page={page_start + page_number}')
            continue
        response_text += response.text

    if not response_text:
        return 'Connection problem. Try again later.'
    # response = requests.get(search_url + letters)
    soup = BeautifulSoup(response_text, 'html.parser')

    word_cards = soup.find_all('div', attrs={'class': 'bTrf rClear'})
    words = []
    for word_card in word_cards:
        word_container = word_card.find('div', attrs={'class': 'rU6px rO0px'})
        word = word_container.find('q').text.replace('\n', '')
        href = base_url + word_container.find('a').get('href')
        english = word_card.find('span', attrs={'lang': 'en'})
        if not english:
            print(f'word {word} ({href}) has no translation.')
            continue
        info_strip = word_card.find('p', attrs={'class': 'rInf rKln r1Zeile rU3px rO0px'})
        level = info_strip.find('span')
        if 'Vocabulary' in level.attrs['title']:
            level = level.text.strip()
            word_type = info_strip.find_all('span')[1].text.strip().capitalize()
        else:
            level = 'Unknown'
            word_type = info_strip.find('span').text.strip().capitalize()
        word_info = {'word': word,
                     'level': level,
                     'word_type': word_type,
                     'english': english.text.replace('\n', '').replace('\xa0', '').replace(',', ', '),
                     'url': href
                     }
        words.append(word_info)
    return words


if __name__ == '__main__':
    # print(get_word_info('schreiben'))
    # print(get_word_info('weiss'))
    # print(get_word_info('es'))
    # print(get_word_info('erschrecken'))
    # print(get_word_info('tisch'))
    # print(get_word_info('regal'))
    # print(get_word_info('das fahren'))
    # print(get_word_info('jogurt'))
    # print(get_wordlist_from_word_search('die'))
    suggestions = get_words_suggestion('die', page_start=2, pages=2)
    print(f'{suggestions=}')
    print(f'{len(suggestions)=}')
