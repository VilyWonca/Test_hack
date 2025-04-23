from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def call_llm(prompt: str) -> str:
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick:free",
        messages=[
            {
            "role": "user",
            "content": prompt
            }
        ]
    )
    return str(completion.choices[0].message.content)

