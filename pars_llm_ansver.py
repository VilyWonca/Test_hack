# parse_llm_response.py

def parse_llm_response(llm_answer: str) -> dict:
    """
    Ищем секции:
      ### New HTML Block
      ### Additional CSS
      ### Additional JS
      ### Explanation
    Возвращаем словарь:
    {
      "new_html": "...",
      "new_css": "...",
      "new_js": "...",
      "explanation": "..."
    }
    """
    sections = {
        "new_html": "",
        "new_css": "",
        "new_js": "",
        "explanation": ""
    }

    lines = llm_answer.splitlines()
    current_key = None

    title_map = {
        "new html block": "new_html",
        "additional css": "new_css",
        "additional js": "new_js",
        "explanation": "explanation"
    }

    for line in lines:
        lower = line.strip().lower()
        if lower.startswith("###"):
            heading = lower.replace("###", "").strip()
            if heading in title_map:
                current_key = title_map[heading]
            else:
                current_key = None
        else:
            if current_key:
                sections[current_key] += line + "\n"

    # Обрезаем
    for k in sections:
        sections[k] = sections[k].strip()

    return sections
