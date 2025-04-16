def apply_llm_changes(context_data: dict, llm_answer: str, css_file: str, js_file: str):
    """
    context_data: {"found_element": old_block, "found_in_file": ... }
    llm_answer: строка от LLM
    css_file, js_file: куда дописываем
    """
    # 1. Парсим ответ
    parsed = parse_llm_response(llm_answer)
    new_html = parsed["new_html"]
    new_css  = parsed["new_css"]
    new_js   = parsed["new_js"]
    explanation = parsed["explanation"]

    # 2. Заменяем HTML
    old_block = context_data["found_element"]
    html_file = context_data["found_in_file"]
    replace_html_block_in_file(html_file, old_block, new_html)

    # 3. Добавляем CSS
    if new_css.strip() and new_css.strip() != "— (нет CSS)":
        append_css(css_file, new_css)

    # 4. Добавляем JS
    if new_js.strip() and new_js.strip() != "— (нет JS)":
        append_js(js_file, new_js)

    # 5. Выводим пояснение
    if explanation.strip():
        print("LLM Explanation:", explanation)
