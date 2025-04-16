# context_builder.py

import os

def build_detailed_prompt(
    user_command: str,
    snippet: str,
    parents: str,
    related_css: str,
    related_js: str
) -> str:
    """
    Формирует развернутый промпт для LLM на основе:
      - user_command: команда пользователя (что изменить)
      - snippet: исходный HTML-блок (outerHTML)
      - parents: HTML-окружение (родительские контейнеры)
      - related_css: CSS, который упоминает классы/id snippet'а
      - related_js: JS, который тоже ссылается на snippet (id/class)
    
    Возвращает одну большую строку (prompt).
    """

    prompt_sections = []

    # 1. Короткое введение
    prompt_sections.append("## Введение\n")
    prompt_sections.append(
        "У нас есть фрагмент HTML-кода, а также его родительский контекст, CSS и JS, "
        "которые потенциально влияют на элемент. Нужно внести изменения "
        "согласно команде пользователя."
    )

    # 2. Сам HTML-блок (snippet)
    prompt_sections.append("\n\n## Исходный HTML-блок (snippet)\n")
    if snippet.strip():
        prompt_sections.append(snippet.strip())
    else:
        prompt_sections.append("— (пусто)")

    # 3. Родительские контейнеры (HTML-окружение)
    prompt_sections.append("\n\n## Родительские контейнеры\n")
    if parents.strip():
        prompt_sections.append(parents.strip())
    else:
        prompt_sections.append("— (нет родительских контейнеров)")

    # 4. Связанный CSS
    prompt_sections.append("\n\n## Связанный CSS\n")
    if related_css.strip():
        prompt_sections.append(related_css.strip())
    else:
        prompt_sections.append("— (нет CSS)")

    # 5. Связанный JS
    prompt_sections.append("\n\n## Связанный JS\n")
    if related_js.strip():
        prompt_sections.append(related_js.strip())
    else:
        prompt_sections.append("— (нет JS)")

    # 6. Команда пользователя
    prompt_sections.append("\n\n## Команда пользователя\n")
    prompt_sections.append(f"{user_command}")

    # 7. Инструкции для LLM
    prompt_sections.append("\n\n## Инструкции\n")
    prompt_sections.append(
        "На основе всего вышеизложенного:\n"
        "1) Обнови/измени HTML-блок так, чтобы удовлетворить требования пользователя.\n"
        "2) Если нужно, добавь/измени CSS. Если добавляешь CSS, укажи в отдельном блоке.\n"
        "3) Если нужно, добавь/измени JS. Тоже укажи отдельно.\n"
        "4) Важно сохранить работоспособность и структуру.\n"
        "5) Верни результат в следующем формате:\n"
        "   ### New HTML Block\n"
        "   <тут обновлённое HTML>\n\n"
        "   ### Additional CSS\n"
        "   <тут css>\n\n"
        "   ### Additional JS\n"
        "   <тут js>\n\n"
        "   ### Explanation\n"
        "   <короткое пояснение, если надо>\n"
    )

    if os.path.dirname("prompt.txt"):
        os.makedirs(os.path.dirname("prompt.txt"), exist_ok=True)
    with open("prompt.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(prompt_sections))
    print("Сохранен промпт предаваемые в LLM")

    return "\n".join(prompt_sections)


def save_full_context_to_file(context: dict, path: str = "context_summary.txt"):
    """
    Сохраняет контекст (найденный элемент, родительские контейнеры, CSS, JS)
    в единый текстовый файл.
    
    Ожидаем, что context = {
      "found_element": str,
      "html_parents": str,
      "related_css": str,
      "related_js": str,
      ... 
    }
    """

    # Убеждаемся, что директория для path существует
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("=== Найденный блок ===\n")
        found_element = context.get("found_element", "") or "—"
        f.write(found_element.strip() + "\n\n")

        f.write("=== Родительская структура ===\n")
        parents = context.get("html_parents", "") or "—"
        f.write(parents.strip() + "\n\n")

        f.write("=== CSS (если найдено) ===\n")
        css_ = context.get("related_css", "") or "—"
        f.write(css_.strip() + "\n\n")

        f.write("=== JS (если найдено) ===\n")
        js_ = context.get("related_js", "") or "—"
        f.write(js_.strip() + "\n\n")

        # Если хотим логировать file_name:
        f.write(f"=== Дополнительно ===\n")
        if "found_in_file" in context:
            f.write(f"Найдено в файле: {context['found_in_file']}\n")

    print(f"✅ Контекст сохранён в файл: {path}")
