import re
from bs4 import BeautifulSoup
import os

def parse_snippet_for_unique_attrs(snippet: str):
    """
    Парсит локально выбранный сниппет (outerHTML),
    пытаясь извлечь его тег, id, data-атрибуты и класс(ы).

    Возвращает словарь, где может быть:
    {
      "tag": "button",
      "id": "myBtn",
      "data_attrs": {"data-foo": "bar"},
      "classes": ["topRight", "special-button"]
    }
    Если каких-то значений нет, в словаре они могут отсутствовать или быть пустыми.
    """
    snippet_soup = BeautifulSoup(snippet, "html.parser")
    
    # Предполагаем, что в snippet - один корневой элемент
    root_elem = snippet_soup.find()  # Первый найденный тег
    
    if not root_elem:
        return {}
    
    result = {}
    result["tag"] = root_elem.name
    
    # Извлекаем id, если есть
    if root_elem.has_attr("id"):
        result["id"] = root_elem["id"]
    
    # Извлекаем классы, если есть
    if root_elem.has_attr("class"):
        result["classes"] = root_elem["class"]  # это список
    
    # Извлекаем data-* атрибуты (если есть)
    data_attrs = {}
    for attr_key, attr_val in root_elem.attrs.items():
        if attr_key.startswith("data-"):
            data_attrs[attr_key] = attr_val
    if data_attrs:
        result["data_attrs"] = data_attrs
    
    return result


def find_element_in_html(html_content: str, snippet_attrs: dict):
    """
    Ищет в html_content элемент, соответствующий тегу и уникальным атрибутам
    (id, data-* и/или классам) из snippet_attrs.
    
    Возвращает объект BeautifulSoup с найденным элементом или None, если не найден.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Начинаем поиск с самого приоритетного: id
    if "id" in snippet_attrs:
        elem_id = snippet_attrs["id"]
        found_by_id = soup.find(snippet_attrs["tag"], id=elem_id)
        if found_by_id:
            return found_by_id
    
    # Если нет id или элемент с таким id не найден, пробуем искать по data-* атрибутам
    # Для этого можем перебирать все теги нужного типа и сравнивать
    if "data_attrs" in snippet_attrs and snippet_attrs["data_attrs"]:
        data_attrs = snippet_attrs["data_attrs"]
        
        # Формируем функцию-предикат для поиска
        def match_data_attrs(tag):
            # Сверяем tag'и
            if tag.name != snippet_attrs["tag"]:
                return False
            # Проверяем все data-* атрибуты на соответствие
            for k, v in data_attrs.items():
                if tag.get(k) != v:
                    return False
            return True
        
        found_by_data = soup.find(match_data_attrs)
        if found_by_data:
            return found_by_data
    
    # Если есть классы - пробуем искать с учётом их
    # Но классы могут быть не уникальны. Если же класс явно уникален,
    # можно прописать селектор. 
    if "classes" in snippet_attrs and snippet_attrs["classes"]:
        # Пробуем совпадение по точному набору классов
        # (при этом на странице могут быть элементы с этим же набором)
        class_list = snippet_attrs["classes"]
        # Можно использовать soup.find_all(...) и отсеивать 
        # тех, у кого ровно те же классы, что и class_list.
        
        candidates = soup.find_all(snippet_attrs["tag"])
        for c in candidates:
            c_classes = c.get("class", [])
            # Проверим, совпадают ли множества
            # Можно проверять строгое равенство набора, 
            # но чаще бывает достаточно хотя бы пересечение
            if set(c_classes) == set(class_list):
                return c
    
    # Если ничего из вышеперечисленного не нашлось,
    # в крайнем случае fallback:
    # - либо возвращаем None,
    # - либо попытка сравнить decode() (но это не так надёжно).
    return None


def analyze_dom_and_collect_context(
        html_filepath: str, 
        selected_snippet: str
    ) -> dict:
    """
    Объединяем два шага:
    1) Парсим snippet, вытаскиваем уникальные атрибуты
    2) В index_current.html ищем соответствующий элемент
    3) Если найден, собираем родительский HTML, CSS и JS, как в предыдущем примере
    Возвращаем структуру контекста для дальнейшей обработки LLM
    """
    
    # 1. Извлечь уникальные атрибуты из selected_snippet
    snippet_attrs = parse_snippet_for_unique_attrs(selected_snippet)
    
    # Читаем содержимое файла
    with open(html_filepath, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 2. Найти элемент в html_content
    found_element_bs = find_element_in_html(html_content, snippet_attrs)
    
    if not found_element_bs:
        # В крайнем случае fallback - сравнение decode()
        # Или возвращаем None
        # (Снизу - пример fallback)
        fallback_el = fallback_decode_search(html_content, selected_snippet)
        if fallback_el:
            found_element_bs = fallback_el
        else:
            return {
                "html_parents": "",
                "related_css": "",
                "related_js": "",
                "found_element": None
            }
    
    # 3. Собираем контекст
    # (используем логику из прошлого примера,
    #  здесь вынесем в отдельные функции для компактности)

    # А. Реконструируем parents
    parents_html_str = collect_parents(found_element_bs)
    # Б. Собираем CSS
    related_css_str = collect_related_css(found_element_bs, html_content)
    # В. Собираем JS
    related_js_str = collect_related_js(found_element_bs, html_content)
    
    return {
        "html_parents": parents_html_str,
        "related_css": related_css_str,
        "related_js": related_js_str,
        "found_element": found_element_bs.decode()
    }


def fallback_decode_search(html_content: str, snippet: str):
    """На случай, если ни id, ни data-* ни класс не сработали, 
    пробуем найти точное совпадение через decode(). 
    """
    soup = BeautifulSoup(html_content, "html.parser")
    all_elems = soup.find_all()
    for el in all_elems:
        if el.decode() == snippet:
            return el
    return None


def collect_parents(elem):
    """Собирает родительские контейнеры (примерно как в прошлом коде)."""
    parents_html = []
    parent = elem.parent
    while parent and parent.name not in ["html", "[document]", None]:
        parents_html.append(parent.decode())
        parent = parent.parent
    return "\n<!-- Parent Container -->\n".join(parents_html[::-1])


def collect_related_css(elem, html_content: str):
    """Аналог предыдущего примера: если есть id/классы, 
    ищем <style>... с упоминанием. 
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    elem_id = elem.get("id")
    elem_classes = elem.get("class", [])
    
    style_tags = soup.find_all("style")
    
    related_css_list = []
    
    id_pattern = None
    if elem_id:
        id_pattern = re.compile(rf'#{elem_id}\b')
    
    class_patterns = [re.compile(rf'\.{cls}\b') for cls in elem_classes]
    
    for st in style_tags:
        css_content = st.string if st.string else ""
        found_any = False
        if id_pattern and id_pattern.search(css_content):
            found_any = True
        if not found_any:
            for cpat in class_patterns:
                if cpat.search(css_content):
                    found_any = True
                    break
        if found_any:
            related_css_list.append(css_content.strip())
    
    return "\n\n<!-- Related CSS -->\n\n".join(related_css_list)


def collect_related_js(elem, html_content: str):
    """Аналог поиска в скриптах."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    elem_id = elem.get("id")
    elem_classes = elem.get("class", [])
    
    script_tags = soup.find_all("script")
    
    id_pattern = re.compile(rf'#{elem_id}\b') if elem_id else None
    class_patterns = [re.compile(rf'\.{cls}\b') for cls in elem_classes]
    
    related_js_list = []
    for sc in script_tags:
        script_content = sc.string if sc.string else ""
        found_any_js = False
        if id_pattern and id_pattern.search(script_content):
            found_any_js = True
        if not found_any_js:
            for cpat in class_patterns:
                if cpat.search(script_content):
                    found_any_js = True
                    break
        if found_any_js:
            related_js_list.append(script_content.strip())
    
    return "\n\n<!-- Related JS -->\n\n".join(related_js_list)

def save_full_context_to_file(context: dict, path: str = "context_summary.txt"): 
    with open(path, "w", encoding="utf-8") as f:
        f.write("=== Найденный блок ===\n")
        f.write((context["found_element"] or "—") + "\n\n")

        f.write("=== Родительская структура ===\n")
        f.write((context["html_parents"] or "—") + "\n\n")

        f.write("=== CSS (если найдено) ===\n")
        f.write((context["related_css"] or "—") + "\n\n")

        f.write("=== JS (если найдено) ===\n")
        f.write((context["related_js"] or "—") + "\n\n")

    print(f"✅ Контекст сохранён в файл: {path}")


# ==== Тестовый запуск ====
if __name__ == "__main__":
    snippet = """<li data-list="bullet" style="">
  <span style="font-weight: 400; color: rgb(255, 255, 255);">Алюминиевый каркас и короб</span>
</li>
"""
    context_data = analyze_dom_and_collect_context("index.html", snippet)
    save_full_context_to_file(context_data)
    if context_data["found_element"]:
        print("==== FOUND ELEMENT ====")
        print(context_data["found_element"])
        print("==== PARENTS ====")
        print(context_data["html_parents"])
        print("==== CSS ====")
        print(context_data["related_css"])
        print("==== JS ====")
        print(context_data["related_js"])
    else:
        print("Element not found")
