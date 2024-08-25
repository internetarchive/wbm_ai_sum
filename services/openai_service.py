import json
import os
from openai import OpenAI
from config.function_schemas import function_schemas
from dotenv import load_dotenv


class OpenAIService:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        load_dotenv()
        self.system_prompt = os.getenv("SYSTEM_PROMPT")

    def get_completion(self, messages):

        # Prepend the system message to the conversation
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=full_messages,
            functions=function_schemas,
            function_call="auto",
            temperature=0.7,
        )
        return response.choices[0].message

    def get_function_args(self, function_call):
        return json.loads(function_call.arguments)
