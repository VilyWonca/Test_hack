# test_replace_in_file.py

def replace_exact_line_in_file(file_path, old_line, new_line):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("🔍 Ищем строку:")
    print(old_line)

    if old_line in content:
        updated = content.replace(old_line, new_line)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print("✅ Строка найдена и заменена.")
    else:
        print("❌ Строка не найдена. Ничего не изменено.")

    # Показываем, что получилось
    with open(file_path, "r", encoding="utf-8") as f:
        print("\n💾 Новый фрагмент файла:")
        print(f.read()[:500])


if __name__ == "__main__":
    old = '<h2 class="t467__title t-title t-title_lg t-margin_auto" field="title" style="color: red;">\n                Фото скрытых дверей в интерьере\n              </h2>'
    new = '<h2 class="t467__title t-title t-title_lg t-margin_auto" field="title" style="color: orange;">\n                Фото скрытых дверей в интерьере\n              </h2>'

    replace_exact_line_in_file("templ/index.html", old, new)

replace_exact_line_in_file('templ/index.html', '<script async="" src="https://mc.yandex.ru/metrika/tag.js"></script>', 'ВОТ ИЗМЕНЕНИЯ')
