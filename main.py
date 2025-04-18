from parser_utils import (
    parse_project_simple,
    load_all_css,
    load_all_js,
    analyze_dom_and_collect_context
)
from indexer_utils import create_css_index, render_css_index_for_llm
from context_builder import (
    build_detailed_prompt,
    save_full_context_to_file
)
from pars_llm_ansver import parse_llm_response
from llm_client import call_llm
from replace_script import apply_html_change, apply_css_change_to_html


def main(user_command: str, snippets: list[str]):
    # 🔹 Собираем сниппет в одну строку
    combined_snippet = "\n".join(snippets)

    root_path = "templ"

    # 🔹 Парсим структуру проекта
    proj = parse_project_simple(root_path)
    all_css = load_all_css("templ/css/")
    all_js  = load_all_js(proj["js_files"])

    # 🔹 Собираем контекст по выбранному элементу
    context_data = analyze_dom_and_collect_context(
        index_html="templ/index.html",          
        all_css=all_css,                     
        all_js=all_js,                       
        selected_snippet=combined_snippet
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
    print(f'Вот изначальные ответ ллм: {llm_answer}')

    def recall_ansver(prompt) -> str:
        rec_prompt = f'''
        Смотри ты сейчас получишь на вход ответ от моей ллм, которая генерит для меня новые блоки кода в виде
        html,css,js.

        Вот ответ от ллм:
        {llm_answer}
        
        Твоя задача пронализировать эти блоки кода и вывести только код под каждым разделом как тут:
        ### New HTML Block
        <p style="text-align: left; color: green">Фурнитура</p>

        ### Additional CSS
        .t-name_lg p {{
            color: green;
        }}

        ### Additional JS
        ""

        ### Explanation
        "Команда пользователя требует изменить цвет текста на зеленый. Поскольку исходный HTML-блок содержал инлайновый стиль, наиболее простым способом выполнить команду было изменить этот стиль напрямую, добавив `color: green`."
        '''
        return call_llm(rec_prompt)
    
    print(f"Вот конечный ответ от ллм: {recall_ansver(llm_answer)}")

    parsed = parse_llm_response(recall_ansver(llm_answer))
    print(f"Вот спарсенный ответ: {parsed}")
    print(f"Вот родительский элемент: {context_data['html_parents']}")

    # 🔹 HTML: обновляем блок в файле
    apply_html_change("templ/index.html", context_data["found_element"], parsed["new_html"])

    # 🔹 CSS: обновляем <style> внутри HTML
    apply_css_change_to_html("templ/index.html", parsed["new_css"])

