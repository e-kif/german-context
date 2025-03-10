import requests
import json
from dotenv import load_dotenv
from data.schemas import ContextSentence, BaseModel
import os
import asyncio

load_dotenv()


class GeneralAnswer(BaseModel):
    question: str
    answer: str


def build_sentence_prompt(topic: str, level: str, words: list[str]) -> str:
    levels = {
        'A1': 'A simple sentence with a subject and verb in the Präsens tense - A1 level',
        'A2': 'A compound sentence that connects two main clauses using a conjunction - A2 level',
        'B1': 'A complex sentence featuring a main clause and a subordinate clause (Nebensatz) - B1 level',
        'B2': 'A complex sentence that uses a subordinate clause to express contrast - B2 level',
        'C1': 'A sophisticated sentence with a relative clause (Relativsatz) '
              'and a conjunction that connects contrasting ideas - C1 level',
        'C2': 'A complex sentence containing an abstract noun, a subordinate clause, '
              'and the ability to express nuanced thoughts clearly - C2 level'
    }
    return (f'Generate a single unique german sentence that have some sense ({levels[level]}) and its exact translation '
            f'into english on topic "{topic}" using all of the following words: {words}')


async def ai_request(prompt: str, model: str = os.getenv('AI_MODEL'), schema: ContextSentence | None = ContextSentence):
    url = 'http://localhost:11434/api/generate'
    data = dict(
        model=model,
        prompt=prompt,
        stream=False,
        options={'temperature': 0.72}
    )
    if schema:
        data['format'] = schema.model_json_schema()
    try:
        response = requests.post(url, data=json.dumps(data))
    except requests.exceptions.ConnectionError:
        return 'Connection problem. Try again later.'
    if response.status_code == 200:
        return json.loads(response.json().get('response'))


if __name__ == '__main__':
    prompt_ = build_sentence_prompt('auto', 'C1', ['Spiegel (Noun)', 'Lenkrad (Noun)'])
    ai = asyncio.run(ai_request(prompt_))
    print(f'{type(ai)=}')
    print(f'{ai}')
