# applier.py
from bs4 import BeautifulSoup
import re


def apply_html_change(html_path, old_outer_html, new_html_block):
    from parser_utils import parse_snippet_for_unique_attrs, find_element_in_html

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    attrs = parse_snippet_for_unique_attrs(old_outer_html)
    target = find_element_in_html(str(soup), attrs)

    if target is None:
        print("[HTML] ❌ Не удалось найти элемент по атрибутам.")
        return

    # Заменяем содержимое
    target.replace_with(BeautifulSoup(new_html_block, "html.parser"))

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print("[HTML] ✅ Элемент найден по атрибутам и заменён.")



def apply_css_change(css_path, new_css_rule):
    if not new_css_rule.strip():
        print("[CSS] Пустое правило — пропускаем.")
        return

    selector_match = re.match(r"^(.*?)\s*\{", new_css_rule.strip(), re.DOTALL)
    if not selector_match:
        print("[CSS] Не удалось извлечь селектор из правила. Добавим как есть.")
        with open(css_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + new_css_rule)
        return

    selector = selector_match.group(1).strip()

    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Паттерн для нахождения уже существующего правила
    pattern = re.compile(rf"{re.escape(selector)}\s*\{{[^{{}}]*?\}}", re.DOTALL)

    if pattern.search(css_content):
        css_content = pattern.sub(new_css_rule, css_content)
        print(f"[CSS] Обновлено правило для селектора: {selector}")
    else:
        css_content += "\n\n" + new_css_rule
        print(f"[CSS] Добавлено новое правило для селектора: {selector}")

    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css_content)


def apply_js_change(js_path, new_js_code):
    if new_js_code.strip().startswith("—") or not new_js_code.strip():
        print("[JS] Код не требуется.")
        return
    with open(js_path, "a", encoding="utf-8") as f:
        f.write("\n\n" + new_js_code)
    print("[JS] Скрипт добавлен в:", js_path)


def apply_all_changes(html_path, old_outer_html, llm_response, css_path, js_path):
    apply_html_change(html_path, old_outer_html, llm_response.get("new_html", ""))
    apply_css_change(css_path, llm_response.get("new_css", ""))
    apply_js_change(js_path, llm_response.get("new_js", ""))
