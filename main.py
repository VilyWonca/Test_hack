# main.py

from parser_utils import (
    parse_project_simple,
    load_all_css,
    load_all_js,
    analyze_dom_and_collect_context,
    find_element_in_html,
    parse_snippet_for_unique_attrs
)
from indexer_utils import create_css_index, render_css_index_for_llm
from context_builder import (
    build_detailed_prompt,
    save_full_context_to_file
)
from pars_llm_ansver import parse_llm_response
from llm_client import call_llm
from replace_script import apply_html_change


def is_local_file(path):
    return not (path.startswith("http://") or path.startswith("https://"))


def main():
    # 1) Корень проекта (здесь указываем путь, где находится index.html и поддиректории css/ и js/)
    root_path = "templ"  # Укажите актуальный путь

    # 2) HTML snippet – выбранный пользователем фрагмент (outerHTML)
    snippet = """<span class="js-feed-post-date t-feed__post-date t-uptitle t-uptitle_xs">15.07.2024</span>""" 

    # 3) Команда пользователя (что требуется изменить)
    user_command = "Сделай этот текста красным"

    # 4) Собираем структуру проекта: index.html, пути к файлам CSS и JS
    proj = parse_project_simple(root_path)
    all_css = load_all_css(proj["css_files"])
    print("Это полная строка CSS", all_css)
    all_js  = load_all_js(proj["js_files"])

    # 5) Анализируем DOM выбранного HTML-файла, собираем контекст выбранного элемента,
    #    включая родительские контейнеры, а также связанные CSS и JS.
    context_data = analyze_dom_and_collect_context(
        index_html="templ/index.html",          
        all_css=all_css,                     
        all_js=all_js,                       
        selected_snippet=snippet
    )
    save_full_context_to_file(context_data, "context_summary.txt")
    if not context_data["found_element"]:
        print("❌ Элемент не найден в index.html")
        return

    # 6) Индексируем CSS-файлы
    css_index = create_css_index(proj["css_files"])
    css_index_str = render_css_index_for_llm(css_index)

    # 7) Формируем prompt
    prompt_text = build_detailed_prompt(
        user_command=user_command,
        snippet=context_data["found_element"],
        parents=context_data["html_parents"],
        related_css=context_data["related_css"],
        related_js=context_data["related_js"],
        css_index_str=css_index_str
    )

    # 8) Получаем ответ от LLM
    llm_answer = call_llm(prompt_text)

    # 9) Парсим результат
    parsed = parse_llm_response(llm_answer)
    print("Ответ в парсе LLM:", parsed)

    # 10) Применяем изменения
    print('Вот старный блок:', context_data["found_element"])
    print('Вот новый блок:', parse_llm_response(llm_answer)['new_html'])
    apply_html_change("templ/index.html", context_data["found_element"], parse_llm_response(llm_answer)['new_html'])
    print('Замена прошла усешно!')
    
if __name__ == "__main__":
    main()
