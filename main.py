from parser_utils import (
    parse_project_simple,
    load_all_css,
    load_all_js,
    analyze_dom_and_collect_context,
    find_element_in_html
)
from indexer_utils import create_css_index, render_css_index_for_llm
from context_builder import (
    build_detailed_prompt,
    save_full_context_to_file
)
from pars_llm_ansver import parse_llm_response
from llm_client import call_llm
from replace_script import apply_html_change, apply_css_change_to_html


def is_local_file(path):
    return not (path.startswith("http://") or path.startswith("https://"))


def main():
    root_path = "templ"

    # 🔹 Исходный HTML-блок
    snippet = """<button class="t-submit" data-buttonfieldset="button" data-field="buttontitle" style="
                                  color: #000000;
                                  background-color: #ffea00;
                                  border-radius: 0px;
                                  -moz-border-radius: 0px;
                                  -webkit-border-radius: 0px;
                                " type="submit">
                                Получить прайс
                              </button>""" 

    user_command = "Сделай цвет кнопки красным"

    # 🔹 Парсим структуру проекта
    proj = parse_project_simple(root_path)
    all_css = load_all_css("templ/css/")
    all_js  = load_all_js(proj["js_files"])

    # 🔹 Собираем контекст по выбранному элементу
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

    # 🔹 Индексируем CSS
    css_index = create_css_index(proj["css_files"])
    css_index_str = render_css_index_for_llm(css_index)

    # 🔹 Строим prompt и отправляем в LLM
    prompt_text = build_detailed_prompt(
        user_command=user_command,
        snippet=context_data["found_element"],
        parents=context_data["html_parents"],
        related_css=context_data["related_css"],
        related_js=context_data["related_js"],
        css_index_str=css_index_str
    )
    llm_answer = call_llm(prompt_text)
    parsed = parse_llm_response(llm_answer)

    print("Ответ от LLM:")
    print(parsed)

    # 🔹 HTML: обновляем блок в файле
    apply_html_change("templ/index.html", context_data["found_element"], parsed["new_html"])
    print("✅ Замена html прошла успешно!")


    # 🔹 CSS: обновляем <style> внутри HTML
    apply_css_change_to_html("templ/index.html", parsed["new_css"])
    print("✅ Замена css прошла успешно!")


if __name__ == "__main__":
    main()
