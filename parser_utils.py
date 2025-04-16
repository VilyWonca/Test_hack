# parser_utils.py
import os
import re
from bs4 import BeautifulSoup


def parse_project_simple(root_path: str) -> dict:
    """
    Предполагаем, что в корневой директории root_path лежат:
      - index.html (главный HTML-файл)
      - Поддиректории, например, css/ и js/ с файлами стилей и скриптами.
    
    Функция находит index.html и извлекает пути к CSS и JS файлам, указанным через теги:
      - <link rel="stylesheet" href="...">
      - <script src="...">
    
    Возвращает словарь следующего вида:
        {
          "index_html": "/полный/путь/index.html",
          "css_files": ["/полный/путь/css/...", ...],
          "js_files":  ["/полный/путь/js/...", ...]
        }
    """
    index_html = os.path.join(root_path, "index.html")

    css_files = []
    js_files = []

    if os.path.exists(index_html):
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()
        soup = BeautifulSoup(content, "html.parser")

        # Ищем CSS файлы по тегу <link rel="stylesheet">
        for link_tag in soup.find_all("link", rel="stylesheet"):
            href = link_tag.get("href")
            if href:
                css_path = os.path.normpath(os.path.join(root_path, href))
                css_files.append(css_path)

        # Ищем JS файлы по тегу <script src="...">
        for script_tag in soup.find_all("script", src=True):
            src = script_tag.get("src")
            if src:
                js_path = os.path.normpath(os.path.join(root_path, src))
                js_files.append(js_path)

    return {
        "index_html": index_html,
        "css_files": css_files,
        "js_files": js_files
    }


def load_all_css(css_files: list) -> str:
    """
    Считывает содержимое каждого CSS-файла из списка css_files и объединяет их в одну большую строку.
    """
    contents = []
    for cfile in css_files:
        if os.path.exists(cfile):
            with open(cfile, "r", encoding="utf-8", errors="ignore") as f:
                contents.append(f.read())
    return "\n".join(contents)


def load_all_js(js_files: list) -> str:
    """
    Считывает содержимое каждого JS-файла из списка js_files и объединяет их в одну строку.
    """
    contents = []
    for jfile in js_files:
        if os.path.exists(jfile):
            with open(jfile, "r", encoding="utf-8", errors="ignore") as f:
                contents.append(f.read())
    return "\n".join(contents)


def parse_snippet_for_unique_attrs(snippet: str) -> dict:
    """
    Принимает HTML-фрагмент (outerHTML выбранного элемента) и извлекает уникальные атрибуты:
      - tag: имя тега
      - id: если присутствует
      - classes: список классов, если присутствуют
      - data_attrs: все атрибуты начинающиеся с "data-"
    
    Возвращает словарь с этими данными.
    """
    snippet_soup = BeautifulSoup(snippet, "html.parser")
    root_elem = snippet_soup.find()  # Предполагаем, что snippet содержит один корневой элемент
    if not root_elem:
        return {}
    result = {"tag": root_elem.name}
    if root_elem.has_attr("id"):
        result["id"] = root_elem["id"]
    if root_elem.has_attr("class"):
        result["classes"] = root_elem["class"]
    data_attrs = {}
    for k, v in root_elem.attrs.items():
        if k.startswith("data-"):
            data_attrs[k] = v
    if data_attrs:
        result["data_attrs"] = data_attrs
    return result


def find_element_in_html(html_content: str, snippet_attrs: dict):
    """
    Ищет элемент в html_content, удовлетворяющий атрибутам, извлеченным из snippet.
    
    Приоритет поиска:
      1) По id (если есть).
      2) По data-* атрибутам.
      3) По точному совпадению набора классов.
    
    Если элемент найден, возвращает объект BeautifulSoup, иначе None.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    if "id" in snippet_attrs:
        found = soup.find(snippet_attrs["tag"], id=snippet_attrs["id"])
        if found:
            return found
    if "data_attrs" in snippet_attrs:
        def match_data_attrs(tag):
            if tag.name != snippet_attrs["tag"]:
                return False
            for dk, dv in snippet_attrs["data_attrs"].items():
                if tag.get(dk) != dv:
                    return False
            return True
        found = soup.find(match_data_attrs)
        if found:
            return found
    if "classes" in snippet_attrs:
        class_list = snippet_attrs["classes"]
        candidates = soup.find_all(snippet_attrs["tag"])
        for c in candidates:
            if set(c.get("class", [])) == set(class_list):
                return c
    return None


def fallback_decode_search(html_content: str, snippet: str):
    """
    Резервный метод поиска: если по уникальным атрибутам элемент не найден,
    сравнивает декодированное содержимое каждого элемента с snippet.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for el in soup.find_all():
        if el.decode() == snippet:
            return el
    return None


def collect_parents(elem, max_levels=4) -> str:
    """
    Собирает родительские контейнеры для элемента, поднимаясь вверх по дереву не более max_levels.
    Возвращает строку, содержащую родительские HTML-контейнеры, разделенные комментарием.
    """
    parents_html = []
    parent = elem.parent
    level = 0
    while parent and parent.name not in ["html", "[document]", None] and level < max_levels:
        parents_html.append(parent.decode())
        parent = parent.parent
        level += 1
    # Разворачиваем список, чтобы самый верхний контейнер был в начале.
    return "\n<!-- Parent Container -->\n".join(parents_html[::-1])


def collect_related_css(elem, all_css: str) -> str:
    """
    Ищет в all_css упоминания id или классов выбранного элемента.
    Если найдено хотя бы одно совпадение, возвращает весь CSS (упрощенно).
    Если совпадений нет, возвращает пустую строку.
    """
    elem_id = elem.get("id")
    elem_classes = elem.get("class", [])
    found_any = False
    if elem_id:
        pattern_id = re.compile(rf'#{re.escape(elem_id)}\b')
        if pattern_id.search(all_css):
            found_any = True
    for cls in elem_classes:
        pattern_class = re.compile(rf'\.{re.escape(cls)}\b')
        if pattern_class.search(all_css):
            found_any = True
    return all_css if found_any else ""


def collect_related_js(elem, all_js: str) -> str:
    """
    Разбивает all_js на строки и возвращает те, в которых упоминается id или класс элемента.
    Если совпадений нет – возвращает пустую строку.
    """
    elem_id = elem.get("id")
    elem_classes = elem.get("class", [])
    lines = all_js.split("\n")
    relevant = []
    found = False
    for line in lines:
        line_str = line.strip()
        if elem_id and elem_id in line_str:
            relevant.append(line)
            found = True
        for cls in elem_classes:
            if cls in line_str:
                relevant.append(line)
                found = True
    return "\n".join(relevant) if found else ""


def analyze_dom_and_collect_context(index_html: str, all_css: str, all_js: str, selected_snippet: str) -> dict:
    """
    Анализирует DOM в index_html, пытаясь найти выбранный элемент по snippet.
    Если элемент найден, собирает:
      - found_element: HTML выбранного элемента,
      - html_parents: родительские контейнеры до max_levels,
      - related_css: CSS, где упоминается id/класс элемента,
      - related_js: JS, где упоминается id/класс элемента,
      - found_in_file: имя файла index_html.
    
    Если элемент не найден – возвращает found_element как None.
    """
    if not os.path.exists(index_html):
        return {
            "found_element": None,
            "html_parents": "",
            "related_css": "",
            "related_js": "",
            "found_in_file": None
        }

    snippet_attrs = parse_snippet_for_unique_attrs(selected_snippet)

    with open(index_html, "r", encoding="utf-8") as f:
        content = f.read()

    found_elem = find_element_in_html(content, snippet_attrs)
    if not found_elem:
        found_elem = fallback_decode_search(content, selected_snippet)
    if not found_elem:
        return {
            "found_element": None,
            "html_parents": "",
            "related_css": "",
            "related_js": "",
            "found_in_file": index_html
        }

    parents_html_str = collect_parents(found_elem, max_levels=4)
    related_css_str = collect_related_css(found_elem, all_css)
    related_js_str = collect_related_js(found_elem, all_js)

    return {
        "found_element": found_elem.decode(),
        "html_parents": parents_html_str,
        "related_css": related_css_str,
        "related_js": related_js_str,
        "found_in_file": index_html
    }
