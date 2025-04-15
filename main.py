from together import Together
from dotenv import load_dotenv
import os
import json
from bs4 import BeautifulSoup

load_dotenv()

client = Together()

api_key = os.getenv("TOGETHER_API_KEY")

def interpret_query(query: str) -> dict:
    prompt = (
         f"Пользовательский запрос: \"{query}\". На основе запроса составь JSON объект с ключами:\n"
        " - tag: название тега (обязательное поле),\n"
        " - id: (если имеется),\n"
        " - class: (если имеется),\n"
        " - text_contains: (если необходимо отфильтровать по содержимому текста),\n"
        " - position_hint: (если есть указание по расположению, например, 'top-right').\n"
        "В ответе дай только корректный JSON в фигурных скобках. Например: {\"tag\": \"button\", \"class\": \"top-nav-button\", \"position_hint\": \"top-right\"}"
    )
    response = client.chat.completions.create(
      model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
      messages=[{"role": "user", "content": prompt}],
    )

    prompt_result = response.choices[0].message.content

    try:
        criteria = json.loads(prompt_result)
    except Exception as e:
        print(f"При парсинге ответа LLM выдало ошибку: {e}")
        print(f'Текст ответа LLM: {prompt_result}')
        criteria = {}

    return criteria

def search_html_block(html_content: str, criteria: dict) -> str:
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    tag = criteria.get("tag")

    if not tag:
        print("Критерии не содержат обязательное поле 'tag'.")
        return None

    # Строим дополнительные атрибуты для поиска
    search_attrs = {}
    if "id" in criteria:
        search_attrs["id"] = criteria["id"]
    if "class" in criteria:
        search_attrs["class"] = criteria["class"]
    
    # Поиск всех элементов заданного тега с дополнительными атрибутами
    candidates = soup.find_all(tag, attrs=search_attrs)
    
    # Если необходимо фильтровать по текстовому содержимому
    text_filter = criteria.get("text_contains")
    if text_filter:
        candidates = [el for el in candidates if text_filter.lower() in el.get_text().lower()]

    # Здесь можно добавить дополнительный анализ, например, по атрибутам inline-стилей для position_hint
    
    if candidates:
        return str(candidates[0])
    else:
        return None

def generate_new_block(old_block: str, modification_instruction: str) -> str:
    """
    Генерирует новый HTML-блок на основе исходного блока и инструкции по изменению.
    
    :param old_block: Строка с исходным HTML-блоком.
    :param modification_instruction: Текстовая инструкция, например, "Перемести кнопку в левый верхний угол".
    :return: Новый HTML-блок.
    """
    prompt = (
        f"Есть следующий HTML-блок:\n{old_block}\n"
        f"Внеси следующие изменения: {modification_instruction}.\n"
        "Верни полностью обновлённый HTML-блок без дополнительных комментариев."
    )
    
    response = client.chat.completions.create(
      model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
      messages=[{"role": "user", "content": prompt}],
    )
    
    new_block = response.choices[0].message.content
    return new_block

def replace_html_block(filename: str, old_block: str, new_block: str) -> None:
    """
    Заменяет первое вхождение old_block в файле filename на new_block.
    
    Аргументы:
      filename: путь к HTML-файлу, который нужно обновить.
      old_block: исходный HTML-блок, который следует заменить.
      new_block: новый HTML-блок, который вставляется вместо старого.
    """
    # Читаем содержимое файла
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Выполняем замену первого вхождения (count=1, чтобы не заменить все совпадения случайно)
    updated_content = content.replace(old_block, new_block, 1)
    
    # Сохраняем обновлённое содержимое обратно в файл (или в новый файл, если нужна резервная копия)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(updated_content)

def main():
    import sys

    # Получаем запрос от пользователя
    query = input("Введите ваш запрос для изменения HTML: ")
    print("\nИнтерпретация запроса с помощью LLM...")
    
    # Получаем критерии для поиска HTML-блока через LLM
    criteria = interpret_query(query)
    if not criteria:
        print("Не удалось получить критерии для поиска из запроса.")
        sys.exit(1)
    
    print("Полученные критерии для поиска:")
    print(criteria)
    
    # Читаем HTML-файл index_current.html
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Файл 'index.html' не найден.")
        sys.exit(1)
    
    # Выполняем поиск HTML-блока по заданным критериям
    old_block = search_html_block(html_content, criteria)
    
    if old_block:
        print("\nНайденный HTML-блок:")
        print(old_block)
    else:
        print("\nПо заданными критериями блок не найден.")

    new_block = generate_new_block(old_block, query)
    print("Новый HTML-блок:")
    print(new_block)

    replace_html_block('index.html', old_block, new_block)
    print('Код успешно изменен!')

  
if __name__ == "__main__":
    main()
