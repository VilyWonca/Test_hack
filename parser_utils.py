import os
import re
from bs4 import BeautifulSoup

def parse_project_simple(root_path: str):
    """
    Предполагаем, что в root_path лежит:
      - index.html
      - папка css/
      - папка js/
    Ищем файлы .css и .js на которые ссылается index.html
    Возвращаем словарь:
    {
      "index_html": "/abs/path/to/index.html",
      "css_files": [...],
      "js_files": [...]
    }
    """
    index_html = os.path.join(root_path, "index.html")
    
    # Если вдруг нужно рекурсивно искать, можно это расширить:
    css_dir = os.path.join(root_path, "css")
    js_dir = os.path.join(root_path, "js")
    
    # Парсим index.html, чтобы узнать подключённые css/js
    css_files = []
    js_files = []
    if os.path.exists(index_html):
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()
        soup = BeautifulSoup(content, "html.parser")
        
        # Ищем <link rel="stylesheet" href="css/...">
        for link_tag in soup.find_all("link", rel="stylesheet"):
            href = link_tag.get("href")
            if href:
                css_path = os.path.join(root_path, href)
                css_path = os.path.normpath(css_path)
                css_files.append(css_path)
        
        # Ищем <script src="js/...">
        for script_tag in soup.find_all("script", src=True):
            src = script_tag.get("src")
            if src:
                js_path = os.path.join(root_path, src)
                js_path = os.path.normpath(js_path)
                js_files.append(js_path)
    
    return {
        "index_html": index_html,
        "css_files": css_files,
        "js_files": js_files
    }

def load_all_css(css_files: list) -> str:
    """
    Считываем содержимое всех .css в одну строку.
    """
    contents = []
    for cfile in css_files:
        if os.path.exists(cfile):
            with open(cfile, "r", encoding="utf-8", errors="ignore") as f:
                contents.append(f.read())
    return "\n".join(contents)

def load_all_js(js_files: list) -> str:
    """
    Считываем содержимое всех .js в одну строку.
    """
    contents = []
    for jfile in js_files:
        if os.path.exists(jfile):
            with open(jfile, "r", encoding="utf-8", errors="ignore") as f:
                contents.append(f.read())
    return "\n".join(contents)

def parse_snippet_for_unique_attrs(snippet: str):
    snippet_soup = BeautifulSoup(snippet, "html.parser")
    root_elem = snippet_soup.find()
    if not root_elem:
        return {}
    result = {"tag": root_elem.name}
    
    if root_elem.has_attr("id"):
        result["id"] = root_elem["id"]
    
    if root_elem.has_attr("class"):
        result["classes"] = root_elem["class"]
    
    data_attrs = {}
    for k,v in root_elem.attrs.items():
        if k.startswith("data-"):
            data_attrs[k] = v
    if data_attrs:
        result["data_attrs"] = data_attrs
    
    return result

def find_element_in_html(html_content: str, snippet_attrs: dict):
    soup = BeautifulSoup(html_content, "html.parser")
    if "id" in snippet_attrs:
        found = soup.find(snippet_attrs["tag"], id=snippet_attrs["id"])
        if found: return found
    if "data_attrs" in snippet_attrs:
        def match_data_attrs(tag):
            if tag.name != snippet_attrs["tag"]:
                return False
            for dk,dv in snippet_attrs["data_attrs"].items():
                if tag.get(dk) != dv:
                    return False
            return True
        found = soup.find(match_data_attrs)
        if found: return found
    if "classes" in snippet_attrs:
        class_list = snippet_attrs["classes"]
        candidates = soup.find_all(snippet_attrs["tag"])
        for c in candidates:
            if set(c.get("class", [])) == set(class_list):
                return c
    return None

def fallback_decode_search(html_content: str, snippet: str):
    soup = BeautifulSoup(html_content, "html.parser")
    for el in soup.find_all():
        if el.decode() == snippet:
            return el
    return None

def collect_parents(elem, max_levels=4):
    parents_html = []
    parent = elem.parent
    level = 0
    while parent and parent.name not in ["html", "[document]", None] and level < max_levels:
        parents_html.append(parent.decode())
        parent = parent.parent
        level += 1
    return "\n<!-- Parent Container -->\n".join(parents_html[::-1])

def collect_related_css(elem, all_css: str):
    """
    Ищем упоминания id/class в all_css
    """
    elem_id = elem.get("id")
    elem_classes = elem.get("class", [])
    results = []
    found_any = False
    
    if elem_id:
        id_pat = re.compile(rf'#{re.escape(elem_id)}\b')
        if id_pat.search(all_css):
            found_any = True
    
    for cls in elem_classes:
        cls_pat = re.compile(rf'\.{re.escape(cls)}\b')
        if cls_pat.search(all_css):
            found_any = True
    
    if found_any:
        # В простом виде - возвращаем весь CSS
        # либо можно искать конкретные селекторы
        results.append(all_css)
    return "\n\n".join(results)

def collect_related_js(elem, all_js: str):
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
    if found:
        return "\n".join(relevant)
    return ""

def analyze_dom_and_collect_context(
    index_html: str,
    all_css: str,
    all_js: str,
    selected_snippet: str
):
    # Парсим snippet -> snippet_attrs
    snippet_attrs = parse_snippet_for_unique_attrs(selected_snippet)
    if not os.path.exists(index_html):
        return {
            "found_element": None,
            "html_parents": "",
            "related_css": "",
            "related_js": ""
        }
    
    # Открываем index.html
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
            "related_js": ""
        }
    
    # Сбор
    parents_html_str = collect_parents(found_elem)
    related_css_str = collect_related_css(found_elem, all_css)
    related_js_str = collect_related_js(found_elem, all_js)
    
    return {
        "found_element": found_elem.decode(),
        "html_parents": parents_html_str,
        "related_css": related_css_str,
        "related_js": related_js_str
    }

# ===== Пример запуска =====

if __name__ == "__main__":
    root_dir = "templ"  # Например, папка, где лежит css/, js/, index.html
    snippet = """
<a class="t-btn t142__submit t-btn_md js-click-stat"
   href="https://drive.google.com/file/d/1Ro15FFz0AQD_zgMVbtk26YhvzeLThJvA/view"
   target="_blank"
   data-tilda-event-name="/tilda/click/rec749775389/button1"
   style="color: #222222; background-color: #...; -webkit-border-radius: 10px;"
   data-buttonfieldset="button"
   rel="noopener">
  <span class="t142__text">Скачать каталог</span>
</a>
""".strip()

    # 1) Получаем структуру
    proj = parse_project_simple(root_dir)
    # 2) Считываем все .css и .js
    all_css = load_all_css(proj["css_files"])
    all_js = load_all_js(proj["js_files"])

    # 3) Анализируем
    context_data = analyze_dom_and_collect_context(
        proj["index_html"], 
        all_css,
        all_js,
        snippet
    )

    # Проверяем
    if context_data["found_element"]:
        print("Элемент найден:")
        print(context_data["found_element"])
    else:
        print("Элемент не найден в index.html")
