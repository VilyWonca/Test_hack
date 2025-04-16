# indexer_utils.py

import os
import re

css_rule_pattern = re.compile(r'(?P<selector>[^\{]+)\{(?P<body>[^\}]+)\}')

def create_css_index(css_files: list) -> list:
    """
    Проходит по каждому CSS-файлу, ищет правила вида:
      selector { body }
    Возвращает список записей, каждая запись содержит:
      - id (уникальный, для ссылки в LLM)
      - filename (откуда правило)
      - selector, body
      - start_line, end_line (приблизительно)
      - original_text (полное правило)
    """
    css_index = []
    global_id = 1

    for cssfile in css_files:
        if not os.path.exists(cssfile):
            continue
        
        with open(cssfile, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        full_text = "".join(lines)

        matches = list(css_rule_pattern.finditer(full_text))
        for match in matches:
            sel = match.group("selector").strip()
            bod = match.group("body").strip()
            original_text = match.group(0)

            # Определяем приблизительную позицию (номер строки)
            start_char = match.start()
            start_line = 1
            current_count = 0
            for i, line in enumerate(lines, start=1):
                current_count += len(line)
                if current_count >= start_char:
                    start_line = i
                    break
            end_line = start_line  # или приблизительно: start_line + 1

            record = {
                "id": global_id,
                "filename": cssfile,
                "selector": sel,
                "body": bod,
                "start_line": start_line,
                "end_line": end_line,
                "original_text": original_text
            }
            css_index.append(record)
            global_id += 1

    return css_index

def render_css_index_for_llm(css_index: list) -> str:
    """
    Создает текстовое представление CSS-индекса для LLM.
    Каждая запись выводится примерно так:
      === CSS Rule #ID
      File: <filename>
      Selector: <selector>
      Body:
         <body>
      Lines: <start_line>-<end_line>
    """
    lines = []
    for rec in css_index:
        lines.append(f"=== CSS Rule #{rec['id']}")
        lines.append(f"File: {rec['filename']}")
        lines.append(f"Selector: {rec['selector']}")
        lines.append("Body:")
        for b in rec["body"].splitlines():
            lines.append("  " + b)
        lines.append(f"Lines: {rec['start_line']}-{rec['end_line']}")
        lines.append("")
    return "\n".join(lines).strip()
