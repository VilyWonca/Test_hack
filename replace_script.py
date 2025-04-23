from bs4 import BeautifulSoup
import re

def apply_html_change(html_path: str, old_html_block: str, new_html_block: str) -> bool:
    """
    Ищет в HTML-файле фрагмент, совпадающий с old_html_block,
    и заменяет его на new_html_block.

    Args:
        html_path (str): Путь к HTML-файлу
        old_html_block (str): Старый HTML-фрагмент, который нужно заменить
        new_html_block (str): Новый HTML-фрагмент, на который произвести замену

    Returns:
        bool: True, если замена произошла, иначе False
    """

    # --- Шаг 1: Чтение исходного HTML ---
    with open(html_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # --- Шаг 2: Парсинг старого и нового фрагментов ---
    old_fragment = BeautifulSoup(old_html_block, "html.parser").find()
    new_fragment = BeautifulSoup(new_html_block, "html.parser").find()

    if old_fragment is None or new_fragment is None:
        print("❌ Один из блоков не содержит валидного HTML-элемента")
        return False

    # --- Шаг 3: Поиск точного совпадения по структуре и содержимому ---
    for tag in soup.find_all(old_fragment.name):
        if str(tag).strip() == str(old_fragment).strip():
            print(f"🕵️ Найден блок для замены:\n{tag}\n")

            tag.replace_with(new_fragment)
            with open(html_path, "w", encoding="utf-8") as file:
                file.write(str(soup))

            print("✅ Замена выполнена успешно.")
            return True

    print("❌ Совпадающий HTML-блок не найден.")
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