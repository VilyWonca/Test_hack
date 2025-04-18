from dotenv import load_dotenv
import together

load_dotenv()  # Загружает .env

def call_llm(prompt: str) -> str:
    client = together.Together()  # API-ключ подтянется автоматически из TOGETHER_API_KEY

    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    return response.choices[0].message.content
