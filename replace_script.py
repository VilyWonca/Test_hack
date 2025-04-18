from bs4 import BeautifulSoup
import re

def apply_html_change(
        html_path: str,
        span_text: str,
        new_html_block: str
    ) -> bool:
        """
        В html_path находит первый <span>, чей .get_text(strip=True) == span_text,
        берёт его родительский <a> и заменяет этот <a> на new_html_block.
        Возвращает True, если замена выполнена, иначе False.
        """
        # ---------- читать файл ----------
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # ---------- разобрать новый фрагмент ----------
        new_anchor = BeautifulSoup(new_html_block, "html.parser").find("a")
        if new_anchor is None:
            print("❌ new_html_block не содержит <a>…</a>")
            return False

        # ---------- найти нужный <span> и его <a> ----------
        for span in soup.find_all("span"):
            if span.get_text(strip=True) == span_text:
                anchor = span.find_parent("a")
                if anchor:
                    print("🕵️ Найден старый <a>:\n", anchor, "\n")

                    # клонируем новый фрагмент, чтобы не переиспользовать один и тот же объект
                    replacement = BeautifulSoup(str(new_anchor), "html.parser").find("a")

                    # ---------- заменить ----------
                    anchor.replace_with(replacement)
                    print("🎉 Заменили на:\n", replacement, "\n")

                    # ---------- сохранить ----------
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    print(f"✅ Заменили ссылку с текстом «{span_text}»")
                    return True

        print(f"❌ Не нашли <span> с текстом «{span_text}»")
        return False

def apply_css_change_to_html(
    index_html_path: str,
    new_css_rule: str
):
    """
    Обновляет или добавляет CSS-правила в HTML-файле.
    
    Параметры:
      index_html_path: путь к HTML-файлу.
      new_css_rule: строка, содержащая одно или несколько CSS-правил (например, 
        ".foo { color: red; } .bar { font-size: 14px; }").
    Логика:
      1) Разбивает вход new_css_rule на отдельные блоки по '}'.
      2) Отбрасывает строки, которые целиком — комментарии.
      3) Для каждого правила:
         a) Извлекает селектор (то, что до '{').
         b) Ищет в <style> этот селектор и заменяет весь блок.
         c) Если не нашёл — добавляет правило в конец последнего <style>,
            или создаёт новый <style> в <head>.
      4) Сохраняет HTML, если были изменения.
    """
    # 1) Подготовка списка правил
    rules = []
    for chunk in new_css_rule.split('}'):
        if '{' in chunk:
            rule = chunk.strip() + '}'
            # 2) пропускаем комментарии вида /* ... */
            if not re.fullmatch(r"\s*/\*.*?\*/\s*", rule, re.DOTALL):
                rules.append(rule)

    if not rules:
        print("[CSS] Пусто или только комментарии — ничего не делаем.")
        return

    # 3) Загружаем HTML
    with open(index_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    style_tags = soup.find_all("style")
    modified = False

    # 3a–c) По каждой чистой паре правило/селектор
    for rule in rules:
        selector_match = re.match(r"^(.*?)\s*\{", rule, re.DOTALL)
        if not selector_match:
            continue
        selector = selector_match.group(1).strip()
        pattern = re.compile(
            rf"{re.escape(selector)}\s*\{{[^{{}}]*?\}}",
            re.DOTALL
        )

        replaced = False
        for tag in style_tags:
            css_text = tag.get_text() or ""
            if pattern.search(css_text):
                new_css = pattern.sub(rule, css_text)
                tag.string = new_css
                print(f"[CSS] Обновлено правило для селектора «{selector}».")
                replaced = True
                modified = True
                break

        if not replaced:
            # 3c) добавляем новое правило
            snippet = "\n\n" + rule + "\n"
            if style_tags:
                last = style_tags[-1]
                last.string = (last.get_text() or "") + snippet
            else:
                head = soup.head or soup.new_tag("head")
                new_tag = soup.new_tag("style")
                new_tag.string = rule
                head.append(new_tag)
                if not soup.head:
                    soup.insert(0, head)
            print(f"[CSS] Добавлено новое правило «{selector}».")
            modified = True

    # 4) Сохраняем, если были изменения
    if modified:
        with open(index_html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"✅[CSS] Файл «{index_html_path}» успешно обновлён.")
    else:
        print("[CSS] Правил для применения не найдено — файл не изменён.")

def apply_js_change(js_path, new_js_code):
    if new_js_code.strip().startswith("—") or not new_js_code.strip():
        print("[JS] Код не требуется.")
        return
    with open(js_path, "a", encoding="utf-8") as f:
        f.write("\n\n" + new_js_code)
    print("[JS] Скрипт добавлен в:", js_path)


def apply_all_changes(html_path, old_outer_html, llm_response, css_path, js_path):
    apply_html_change(html_path, old_outer_html, llm_response.get("new_html", ""))
    apply_css_change_to_html(css_path, llm_response.get("new_css", ""))
    apply_js_change(js_path, llm_response.get("new_js", ""))