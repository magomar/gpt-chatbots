import os

import openai
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(raise_error_if_not_found=True))

openai.api_key  = os.getenv('OPENAI_API_KEY')


def create_gpt_completion(ai_model: str, temperature: float, messages: list[dict]) -> dict:
    return openai.ChatCompletion.create(
        model=ai_model,
        messages=messages,
        temperature=temperature
    )