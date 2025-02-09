import requests
import json
from dotenv import load_dotenv
from data.schemas import BaseModel
from typing import Type
import os

load_dotenv()


class GeneralAnswer(BaseModel):
    question: str
    answer: str


def ai_request(prompt: str, model: str, schema: Type[BaseModel] | None):
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
        return response.json().get('response')


if __name__ == '__main__':
    ai = ai_request('why are the roses red?', os.getenv('AI_MODEL'), GeneralAnswer)
    print(ai)
