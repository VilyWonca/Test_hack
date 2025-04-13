import argparse
import requests

def load_path(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def get_llm_response(prompt):
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "max_tokens": 1024,
        "stream": False,
        "temperature": 0.2
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(f"Ошибка при вызове LLM: {response.status_code} {response.text}")

    result = response.json()

    return result['response']
    

def main():
    parser = argparse.ArgumentParser(description="Генерация промпт для ML генерации кода")
    parser.add_argument("--html", required=True, help="Путь к input.html")
    parser.add_argument("--css", required=True, help="Путь к input.css")
    parser.add_argument("--js", required=True, help="Путь к input.js")
    parser.add_argument("--query", required=True, help="Путь к user_query.txt")
    parser.add_argument("--prompt", default="samples/defoult_prompt.txt", help="Путь к defoult_prompt.txt")

    args = parser.parse_args()

    html = load_path(args.html)
    css = load_path(args.css)
    js = load_path(args.js)
    user_query = load_path(args.query)
    template = load_path(args.prompt)

    prompt = template.format(html=html, css=css, js=js, user_query=user_query)

    print("PROMPT START")
    print(prompt)
    print("PROMPT END")

    print("Отправка запроса в LLM:")

    try:
        print("Генерация ответа")
        llm_response = get_llm_response(prompt)
        print(llm_response)
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":  
    main()