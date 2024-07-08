import json
from openai import OpenAI
from config.function_schemas import function_schemas


class OpenAIService:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_completion(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=function_schemas,
            function_call="auto",
        )
        return response.choices[0].message

    def get_function_args(self, function_call):
        return json.loads(function_call.arguments)
