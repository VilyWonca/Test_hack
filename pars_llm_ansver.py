import re

def parse_llm_response(llm_answer: str) -> dict:
    """
    Ищет секции в тексте:
      ### New HTML Block
      ### Additional CSS
      ### Additional JS
      ### Explanation
    Возвращает словарь, например:
    {
      "new_html": "...",
      "new_css": "...",
      "new_js": "...",
      "explanation": "..."
    }
    """
    # Простая реализация: регуляркой найдём блоки между ### <something> и ### <something else>.
    # Или делим построчно, ищем заголовки, копим текст до следующего заголовка.
    
    sections = {
        "new_html": "",
        "new_css": "",
        "new_js": "",
        "explanation": ""
    }
    
    # Для удобства делаем "current_section" = None
    lines = llm_answer.splitlines()
    current_key = None
    
    # Карта заголовков -> ключа словаря
    title_map = {
        "new html block": "new_html",
        "additional css": "new_css",
        "additional js": "new_js",
        "explanation": "explanation"
    }
    
    for line in lines:
        line_lower = line.strip().lower()
        
        # Если встретили линию типа "### New HTML Block"
        if line_lower.startswith("###"):
            # вырезаем "###"
            heading = line_lower.replace("###", "").strip()
            # проверяем, есть ли в title_map
            if heading in title_map:
                current_key = title_map[heading]
            else:
                # Неизвестный заголовок, сбрасываем
                current_key = None
        else:
            # Если мы уже в секции, добавляем содержимое
            if current_key:
                sections[current_key] += line + "\n"
    
    # Уберём лишние пробелы
    for k,v in sections.items():
        sections[k] = v.strip()
    
    return sections
