import requests
from bs4 import BeautifulSoup
from random import randint


def get_soup_for_word(word: str) -> BeautifulSoup:
    base_url = 'https://www.woerter.net/?w='
    response = requests.get(base_url + word.replace(' ', '+'))
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup


def get_soup_from_url(url: str) -> BeautifulSoup:
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup


def get_word_from_soup(soup: BeautifulSoup) -> tuple[str, BeautifulSoup | None]:
    word = soup.find('div', attrs={'class': 'rCntr rClear'})
    if word:
        if '\n' in word.text.strip():
            parts_new = word.text.replace('\n', '').split(',')
            if len(parts_new) == 2:
                return ' '.join(parts_new[::-1]), soup
            the_word = parts_new[0]
            article = ", ".join([art.strip() for art in parts_new if art.strip()[0] == art.strip()[0].lower()])
            return f'{article} {the_word}', soup
        return word.text.strip(), soup
    url_object = soup.find('a', attrs={'class': 'rKnpf rNoSelect rKnUnt rKnObn'})
    if not url_object:
        return soup.find('i').text.strip(), None
    new_url = url_object.attrs['href']
    if 'http' not in new_url:
        new_url = 'https://woerter.net' + new_url
    soup = get_soup_from_url(new_url)
    return soup.find('div', attrs={'class': 'rCntr rClear'}).text.strip(), soup


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
    return [example1, example2]


def get_word_info(word: str) -> dict | str:
    soup = get_soup_for_word(word)
    word, soup = get_word_from_soup(soup)
    if not soup:
        return word
    word_info = {'word': word}
    level, word_type = get_word_level_and_type(soup)
    translation = get_word_translation(soup)
    example = get_word_example(soup)
    if level and word_type:
        word_info.update({'level': level, 'word_type': word_type})
    if translation:
        word_info.update({'translation': translation})
    if example:
        word_info.update({'example': example})
    return word_info


if __name__ == '__main__':
    # print(get_word_info('schreiben'))
    # print(get_word_info('weiss'))
    # print(get_word_info('es'))
    print(get_word_info('erschrecken'))
    # print(get_word_info('tisch'))
    # print(get_word_info('regal'))
    # print(get_word_info('das fahren'))
    # print(get_word_info('jogurt'))
