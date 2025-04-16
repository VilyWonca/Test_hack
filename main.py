from parser_utils import (
    parse_project_simple, load_all_css, load_all_js,
    analyze_dom_and_collect_context
)
from context_builder import build_detailed_prompt, save_full_context_to_file
from llm_client import call_llm
from pars_llm_ansver import parse_llm_response

def main():
    # Шаг 1: Задаём путь к проекту напрямую в коде
    root_path = "templ"  # Пример, укажите свой реальный путь
    
    # Шаг 2: Задаём сниппет (outerHTML) вручную
    snippet = """<h2 class="t467__title t-title t-title_lg t-margin_auto" field="title">
  Фото скрытых дверей в интерьере
</h2>""".strip()
    
    # Шаг 3: Формируем пользовательскую команду
    user_command = "Сделай цвет текста не черным, а красным"

    # Шаг 4: Парсим структуру (index.html, css/, js/)
    project_info = parse_project_simple(root_path)
    all_css = load_all_css(project_info["css_files"])
    all_js  = load_all_js(project_info["js_files"])

    # Шаг 5: Анализ DOM + контекст
    context_data = analyze_dom_and_collect_context(
        project_info["index_html"],
        all_css,
        all_js,
        snippet
    )

    # Сохраняем промежуточный контекст (необязательно, но полезно для отладки)
    save_full_context_to_file(context_data, path="prompt.txt")
    
    if not context_data["found_element"]:
        print("Элемент не найден в index.html.")
        return
    
    # Шаг 6: Формируем prompt для LLM
    prompt_text = build_detailed_prompt(
        user_command,
        snippet=context_data["found_element"],
        parents=context_data["html_parents"],
        related_css=context_data["related_css"],
        related_js=context_data["related_js"]
    )

    # Шаг 7: Отправляем prompt в LLM
    answer = call_llm(prompt_text)

    # Шаг 8: Выводим ответ
    print("=== LLM ANSWER ===")
    print(answer)

    print('Парсим ответ LLM')
    print(parse_llm_response(answer))

if __name__ == "__main__":
    main()
