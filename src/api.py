from src.config import OPENAI_API_KEY
from openai import OpenAI

class OpenAIApi:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def get_client(self):
        return self.client