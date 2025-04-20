# parser_utils.py
import os
import re
from bs4 import BeautifulSoup
from typing import Dict, List
import sys
from pathlib import Path

def parse_project_simple(index_html_path: str) -> dict:
    """
    Принимает путь к index.html и извлекает пути к CSS и JS файлам.

    Возвращает:
    {
        "index_html": полный путь,
        "css_files": список css файлов (полные пути),
        "js_files": список js файлов (полные пути)
    }
    """
    index_html = Path(index_html_path)

    if not index_html.exists():
        raise FileNotFoundError(f"❌ Файл не найден: {index_html_path}")
    if not index_html.name.endswith(".html"):
        raise ValueError("❌ Указанный файл не является .html")

    css_files = []
    js_files = []

    with open(index_html, "r", encoding="utf-8") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")

    # Ищем <link rel="stylesheet" href=...>
    for link_tag in soup.find_all("link", rel="stylesheet"):
        href = link_tag.get("href")
        if href:
            css_path = (index_html.parent / href).resolve()
            css_files.append(str(css_path))

    # Ищем <script src=...>
    for script_tag in soup.find_all("script", src=True):
        src = script_tag.get("src")
        if src:
            js_path = (index_html.parent / src).resolve()
            js_files.append(str(js_path))

    return {
        "index_html": str(index_html.resolve()),
        "css_files": css_files,
        "js_files": js_files
    }


def load_all_css(css_dir: str) -> str:
    """
    Считывает все CSS-файлы из указанной директории и объединяет их содержимое в одну строку.
    """
    contents = []
    for filename in os.listdir(css_dir):
        if filename.lower().endswith(".css"):
            filepath = os.path.join(css_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
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



from bs4 import BeautifulSoup
import sys

def find_element_in_html(html_content: str, selected_snippet: str):
    """
    Ищет элемент из selected_snippet в полном html_content:
    - Сравнивает тег
    - Атрибуты (id, class, data-*, field и т.д.)
    - Внутренний текст
    
    Если находит совпадение — возвращает этот элемент из html_content.
    Если нет — выводит ошибку и завершает выполнение.
    """
    # Подготовка
    cleaned_snippet = "\n".join([line.strip() for line in selected_snippet.splitlines()])
    cleaned_html = "\n".join([line.strip() for line in html_content.splitlines()])

    if cleaned_snippet not in cleaned_html:
        print("❌ Не удалось найти сниппет в HTML.")
        sys.exit(1)

    # Парсим оба HTML
    soup = BeautifulSoup(html_content, "html.parser")
    snippet_soup = BeautifulSoup(selected_snippet, "html.parser")

    # Извлекаем из сниппета данные
    target = snippet_soup.find()
    tag_name = target.name
    attrs = target.attrs
    inner_text = target.get_text(strip=True)

    # Поиск по полному DOM
    candidates = soup.find_all(tag_name)
    for c in candidates:
        # Проверка на совпадение атрибутов
        if all(c.get(k) == v for k, v in attrs.items()):
            # Проверка текста (чтобы не спутать похожие теги)
            if c.get_text(strip=True) == inner_text:
                return c

    print("❌ Сниппет найден как текст, но не удалось найти элемент через BeautifulSoup.")
    sys.exit(1)


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


def collect_parents(elem, max_length=1500) -> str:
    """
    Возвращает HTML ближайшего родителя, если он не превышает max_length.
    Иначе возвращает пустую строку.
    """
    parent = elem.parent
    if parent and parent.name not in ["html", "[document]", None]:
        html = parent.decode()
        if len(html) <= max_length:
            return html
    return elem



import re

def collect_related_css(elem, index_html_path: str) -> str:
    """
    Извлекает CSS-правила из index.html и возвращает строку с CSS-блоками, 
    релевантными переданному элементу.
    """
    elem_id = elem.get("id")
    elem_classes = elem.get("class", [])

    if not elem_id and not elem_classes:
        return ""

    with open(index_html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Собираем CSS из всех тегов <style>
    style_tags = soup.find_all("style")
    all_css = "\n".join(tag.get_text() for tag in style_tags)

    pattern_parts = []
    if elem_id:
        pattern_parts.append(fr'#{re.escape(elem_id)}\b')
    for cls in elem_classes:
        pattern_parts.append(fr'\.{re.escape(cls)}\b')

    pattern_str = "|".join(pattern_parts)
    css_rule_pattern = re.compile(r'([^{]+)\{([^}]+)\}', re.MULTILINE)

    relevant_blocks = []
    for match in css_rule_pattern.finditer(all_css):
        selector, body = match.groups()
        if re.search(pattern_str, selector):
            relevant_blocks.append(f"{selector.strip()} {{{body.strip()}}}")

    return "\n\n".join(relevant_blocks)


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
    Анализирует DOM из index.html, находит selected_snippet и возвращает:
      - найденный HTML элемент,
      - родительские контейнеры,
      - CSS-правила, связанные с id/class,
      - JS-фрагменты, связанные с id/class,
      - путь к index.html (как маркер источника).
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

    # Поиск элемента
    found_elem = find_element_in_html(content, selected_snippet)
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

    # Собираем окружение
    parents_html_str = str(collect_parents(found_elem))
    related_css_str = collect_related_css(found_elem, index_html)  # ✅ используем переданный index_html
    related_js_str = collect_related_js(found_elem, all_js)

    return {
        "found_element": found_elem.decode(),
        "html_parents": parents_html_str,
        "related_css": related_css_str,
        "related_js": related_js_str,
        "found_in_file": index_html
    }

