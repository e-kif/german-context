import requests
import json
from dotenv import load_dotenv
from data.schemas import ContextSentence, BaseModel
from typing import Type
import os

load_dotenv()


class GeneralAnswer(BaseModel):
    question: str
    answer: str


def build_sentence_prompt(topic: str, level: str, words: list[str]) -> str:
    return f'Generate unique german sentence ({level} level) and its exact translation into english on topic "{topic}" using all of the following words: {words}'


async def ai_request(prompt: str, model: str = os.getenv('AI_MODEL'), schema: ContextSentence | None = ContextSentence):
    url = 'http://localhost:11434/api/generate'
    data = dict(
        model=model,
        prompt=prompt,
        stream=False
    )
    if schema:
        data['format'] = schema.model_json_schema()
    response = requests.post(url, data=json.dumps(data))
    if response.status_code == 200:
        return json.loads(response.json().get('response'))


if __name__ == '__main__':
    prompt_ = build_sentence_prompt('auto', 'C1', ['Spiegel (Noun)', 'Lenkrad (Noun)'])
    ai = ai_request(prompt_)
    print(f'{type(ai)=}')
    print(f'{ai}')
