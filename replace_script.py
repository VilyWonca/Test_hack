from bs4 import BeautifulSoup
import re

def apply_html_change(html_path, old_outer_html, new_html_block):
    print("[HTML] Пытаемся обновить:", html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    if old_outer_html in html_content:
        updated = html_content.replace(old_outer_html, new_html_block)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(updated)

        print("✅ ЗАМЕНА ВЫПОЛНЕНА ЧЕРЕЗ str.replace")
    else:
        print("❌ СТРОКА НЕ НАЙДЕНА В ФАЙЛЕ — ЗАМЕНА НЕ ПРОИЗОШЛА")


import re
from bs4 import BeautifulSoup

def apply_css_change_to_html(index_html_path: str, new_css_rule: str):
    if not new_css_rule.strip():
        print("[CSS] Пустое новое правило — пропускаем.")
        return

    with open(index_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    style_tags = soup.find_all("style")
    rule_updated = False

    # 1. Пытаемся найти и заменить по селектору
    selector_match = re.match(r"^(.*?)\\s*\\{", new_css_rule.strip(), re.DOTALL)
    if selector_match:
        selector = selector_match.group(1).strip()
        selector_regex = re.compile(rf"{re.escape(selector)}\\s*\\{{[^{{}}]*?\\}}", re.DOTALL)

        for style_tag in style_tags:
            css_content = style_tag.string or ""
            if selector_regex.search(css_content):
                css_content_updated = selector_regex.sub(new_css_rule.strip(), css_content)
                style_tag.string.replace_with(css_content_updated)
                rule_updated = True
                print(f"[CSS] Обновлено правило по селектору '{selector}'.")
                break

    # 2. Если не нашли — добавляем новое правило
    if not rule_updated:
        if style_tags:
            last_style_tag = style_tags[-1]
            last_style_tag.string = (last_style_tag.string or "") + "\\n\\n" + new_css_rule.strip() + "\\n"
        else:
            head = soup.head or soup.new_tag("head")
            new_style_tag = soup.new_tag("style")
            new_style_tag.string = new_css_rule.strip()
            head.append(new_style_tag)
            if not soup.head:
                soup.html.insert(0, head)
        print("[CSS] Правило не найдено — добавлено новое правило.")

    # 3. Сохраняем изменения
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))




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