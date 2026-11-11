# Приложение Б. Функции выражений

Сгенерировано `tools/author_docs.py appendices` из справочника транслятора; не править вручную.

## Числа

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `num(x, digits=None, lang)` | число по правилам языка: группы разрядов, запятая | `num(12500, digits=2) → "12 500,00"` | библ. 2 |
| `percent(x, digits=None, lang)` | процент с неразрывным пробелом: «20 %» | `percent(20) → "20 %"` | библ. 2 |
| `round_to(x, step)` | округлить до шага, половина от нуля | `round_to(1234, 50) → 1250` | библ. 2 |
| `ceil_to(x, step)` | округлить до шага вверх | `ceil_to(1201, 100) → 1300` | библ. 2 |
| `floor_to(x, step)` | округлить до шага вниз | `floor_to(1299, 100) → 1200` | библ. 2 |
| `round_money(x)` | округлить до сотых, половина от нуля | `round_money(dec("10.005")) → 10.01` | библ. 2 |
| `round(x, ndigits=None)` | округлить, половина от нуля; без ndigits — целое | `round(2.675, 2) → 2.68` | 12.4 |
| `abs(x)` | модуль числа | `abs(-5) → 5` | 12.10 |
| `min(*values, key, default)` | наименьшее из аргументов или списка | `min(3, 1, 2) → 1` | 12.10 |
| `max(*values, key, default)` | наибольшее из аргументов или списка | `max([3, 1, 2]) → 3` | 12.10 |
| `sum(seq, start=0)` | сумма списка | `sum([1.50, 2.25]) → 3.75` | 12.10 |
| `dec(x)` | в decimal (из float — кратчайшая десятичная запись) | `dec(0.1) → 0.1` | 12.4 |
| `float(x)` | в float; datetime даёт серийное число | `float("2.5") → 2.5` | 12.4 |
| `int(x)` | отбросить дробную часть (decimal с масштабом 0) | `int(7.9) → 7` | 12.4 |

## Деньги и НДС

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `money(x, code, currency_style="short", lang)` | сумма с валютой: «12 500,00 грн» | `money(12500, "UAH") → "12 500,00 грн"` | библ. 3 |
| `money_words(x, code, kop="digits", cap=False, lang)` | сумма прописью | `money_words(12500, "UAH") → "двенадцать тысяч пятьсот гривен 00 копеек"` | библ. 3 |
| `money_full(x, code, kop="digits", cap=False, currency_style="short", lang)` | сумма цифрами и прописью в скобках (договорная форма) | `money_full(12500.50, "UAH") → "12 500,50 грн (двенадцать тысяч пятьсот гривен 50 копеек)"` | библ. 3 |
| `vat(x, rate)` | налог с суммы без налога | `vat(1000, 20) → 200.00` | библ. 3 |
| `with_vat(x, rate)` | сумма с налогом | `with_vat(1000, 20) → 1200.00` | библ. 3 |
| `vat_in(x, rate)` | налог, содержащийся в сумме с налогом | `vat_in(1200, 20) → 200.00` | библ. 3 |
| `without_vat(x, rate)` | сумма без налога из суммы с налогом | `without_vat(1200, 20) → 1000.00` | библ. 3 |
| `split(total, shares)` | разделить сумму по долям; части дают сумму | `split(100, [1, 1, 1]) → [33.33, 33.33, 33.34]` | библ. 3 |

## Прописью

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `words(x, code=None, gender="m", case="nom", lang)` | число прописью; words(x, "UAH") — сумма | `words(21, gender="f") → "двадцать одна"` | библ. 4 |
| `ordinal(n, gender="m", case="nom", lang)` | порядковое числительное прописью | `ordinal(21, case="gen") → "двадцать первого"` | библ. 4 |
| `date_words(dt, lang)` | дата прописью | `date_words(date(2026, 10, 12)) → "двенадцатого октября две тысячи двадцать шестого года"` | библ. 4 |

## Даты и время

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `date(y, m, d)` | дата: date(y, m, d) или date("YYYY-MM-DD") | `date(2026, 10, 12) → date("2026-10-12")` | 12.3 |
| `datetime(y, m, d, h=0, mi=0, s=0)` | момент: datetime(y, m, d, h, mi, s), строка ISO или серийное число | `datetime("2026-10-12T14:30") → datetime("2026-10-12T14:30:00")` | 12.3 |
| `build_date()` | дата начала сборки (--build-date, build_date: проекта) | `build_date() → date("2026-10-12")` | 12.7 |
| `weeks(n)` | число суток в n неделях: dt + weeks(2) | `weeks(2) → 14` | библ. 5 |
| `hours(n)` | число суток в n часах: dt + hours(36) | `hours(36) → 1.5` | библ. 5 |
| `minutes(n)` | число суток в n минутах | `date(2026, 10, 12) + minutes(90) → datetime("2026-10-12T01:30:00")` | библ. 5 |
| `add_months(dt, n)` | сдвиг на месяцы (31 → последний день месяца) | `add_months(date(2026, 1, 31), 1) → date("2026-02-28")` | библ. 5 |
| `add_years(dt, n)` | сдвиг на годы | `add_years(date(2028, 2, 29), 1) → date("2029-02-28")` | библ. 5 |
| `fmt_date(dt, format="short", lang)` | дата текстом: short, long, contract или шаблон (ДСТУ 4163:2020) | `fmt_date(date(2026, 10, 12), "contract") → "«12» октября 2026 г."` | библ. 5 |
| `fmt_time(dt, format="short", lang)` | время текстом: short или шаблон {hh}:{mi} | `fmt_time(datetime(2026, 10, 12, 14, 30, 0)) → "14:30"` | библ. 5 |
| `fmt_datetime(dt, format="short", lang)` | дата и время текстом | `fmt_datetime(datetime(2026, 10, 12, 14, 30, 0), "long") → "12 октября 2026 года, 14:30"` | библ. 5 |
| `weekday(dt, case="nom", lang)` | название дня недели (падеж nom или acc) | `weekday(date(2026, 10, 12)) → "понедельник"` | библ. 5 |
| `month_name(dt, case="nom", lang)` | название месяца (падеж nom, gen, loc) | `month_name(date(2026, 10, 12), case="gen") → "октября"` | библ. 5 |
| `is_workday(dt, calendar)` | рабочий ли день (по календарю проекта) | `is_workday(date(2026, 10, 10)) → False` | библ. 5 |
| `workdays(dt, n, calendar)` | дата через n рабочих дней после dt (n < 0 — до) | `workdays(date(2026, 10, 9), 1) → date("2026-10-12")` | библ. 5 |

## Единицы и длины

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `qty(x, unit, tol, digits=None, lang)` | значение с единицей: «230 В», tol= — допуск | `qty(230, "V") → "230 В"` | библ. 6 |
| `qty_range(low, high, unit, digits=None, lang)` | диапазон с единицей: «100–240 В» | `qty_range(-20, 55, "degC") → "−20…+55 °C"` | библ. 6 |
| `convert(x, from, to)` | пересчитать между единицами одной величины | `convert(1.5, "kW", "W") → 1500` | библ. 6 |
| `length(text)` | длина из строки: length("10mm") | `length("10mm") + 5*mm → length("15mm")` | 12.3 |
| `mm` | константа длины: 10*mm | `10*mm → length("10mm")` | 12.3 |
| `cm` | константа длины: 10*cm | `10*cm → length("10cm")` | 12.3 |
| `pt` | константа длины: 10*pt | `10*pt → length("10pt")` | 12.3 |
| `inch` | константа длины: 10*inch | `10*inch → length("10inch")` | 12.3 |

## Текст

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `plural(n, *forms, frac, lang)` | форма слова по числу: plural(n, "день", "дня", "дней") | `plural(5, "день", "дні", "днів", lang="uk") → "днів"` | библ. 7 |
| `join_list(items, last, sep=", ", lang)` | соединить список: «А, Б и В» | `join_list(["А", "Б", "В"], last="та") → "А, Б та В"` | библ. 7 |
| `cap(s)` | заглавная первая буква | `cap("київ") → "Київ"` | библ. 7 |
| `translit(s, lang)` | транслитерация (uk — постановление КМУ № 55, ru — ICAO Doc 9303) | `translit("Згорани", lang="uk") → "Zghorany"` | библ. 7 |
| `sort_key(s, lang)` | ключ сортировки по алфавиту языка: sorted(names, key=sort_key) | `sorted(["Ґава", "Гора", "Єва", "Есе"], key=sort_key) → ['Гора', 'Есе', 'Єва', 'Ґава']` | библ. 7 |
| `nbsp_short(s, lang)` | неразрывный пробел после коротких предлогов и союзов | `nbsp_short("в домі та у дворі", lang="uk") → "в домі та у дворі"` | библ. 7 |
| `str(x)` | значение строкой (даты — ISO, числа — с точкой) | `str(2.20) → "2.20"` | 12.10 |
| `repr(x)` | значение в виде кода | `repr("a") → "'a'"` | 12.10 |

## Списки и записи

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `len(seq)` | длина: символы, элементы, ключи | `len("Київ") → 4` | 12.10 |
| `range(start, stop, step=1)` | числа от start до stop (не включительно) с шагом | `range(1, 10, 3) → [1, 4, 7]` | 12.10 |
| `enumerate(seq, start=0)` | пары (номер, элемент) | `enumerate(["a", "b"], start=1) → [(1, 'a'), (2, 'b')]` | 12.10 |
| `zip(*lists)` | кортежи элементов с одинаковым индексом | `zip([1, 2], ["a", "b"]) → [(1, 'a'), (2, 'b')]` | 12.10 |
| `sorted(seq, key, reverse=False)` | отсортированный список | `sorted([3, 1, 2]) → [1, 2, 3]` | 12.10 |
| `reversed(seq)` | список в обратном порядке | `reversed([1, 2, 3]) → [3, 2, 1]` | 12.10 |
| `any(seq)` | есть ли хоть один истинный элемент | `any([0, 1]) → True` | 12.10 |
| `all(seq)` | все ли элементы истинны | `all([1, 2]) → True` | 12.10 |
| `list(seq)` | список (из последовательности) | `list("abc") → ['a', 'b', 'c']` | 12.10 |
| `tuple(seq)` | кортеж | `tuple([1, 2]) → (1, 2)` | 12.10 |
| `dict(source=None, **items)` | словарь: из пар, записи или key=value | `dict(a=1, b=2) → {'a': 1, 'b': 2}` | 12.10 |
| `record(source=None, **fields)` | запись с доступом через точку: r.name | `record(name="Кабель", qty=3) → record(name='Кабель', qty=3)` | 12.6 |
| `bool(x)` | логическое значение | `bool("") → False` | 12.10 |
| `getattr(r, name, default)` | поле записи по имени, со значением по умолчанию | `getattr(record(a=1), "b", 0) → 0` | 12.6 |
| `hasattr(r, name)` | есть ли у записи поле | `hasattr(record(a=1), "a") → True` | 12.6 |
| `type(x)` | имя типа: "decimal", "str", "datetime"… | `type(1.5e3) → "float"` | 12.3 |

## Данные

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `group_by(items, key)` | словарь «значение ключа → список записей» | `group_by([record(k="a", v=1), record(k="a", v=2)], "k") → {'a': [record(k='a', v=1), record(k='a', v=2)]}` | библ. 8 |
| `sum_by(items, key, value)` | суммы поля по группам | `sum_by([record(k="a", v=1), record(k="a", v=2)], "k", "v") → {'a': 3}` | библ. 8 |
| `distinct(items, key)` | уникальные значения поля | `distinct([record(k="a"), record(k="b"), record(k="a")], "k") → ['a', 'b']` | библ. 8 |
| `load_csv(path, types, sep)` | строки файла CSV как записи | `load_csv("data/items.csv")` | 10.5 |
| `load_yaml(path)` | данные файла YAML (записи и списки) | `load_yaml("data/order.yaml")` | 10.5 |
| `load_json(path)` | данные файла JSON | `load_json("data/order.json")` | 10.5 |
| `load_text(path)` | весь текстовый файл как строка (UTF-8; например, SVG для \|img(svg=…)) | `load_text("img/sign.svg")` | 10.5 |
| `load_ods(path, sheet, range, header=True, types)` | строки листа файла ODS как записи (сохранённые результаты формул) | `load_ods("data/items.ods", sheet="Позиції")` | 10.5 |
| `load_xlsx(path, sheet, range, header=True, types)` | строки листа файла XLSX как записи (сохранённые результаты формул) | `load_xlsx("data/items.xlsx", sheet="Позиції")` | 10.5 |

## Математика (std/math)

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `math.sqrt(x)` | квадратный корень; в документе: \|import("std/math") | `math.sqrt(2) → 1.4142135623730951` | библ. 9 |
| `math.exp(x)` | e в степени x; в документе: \|import("std/math") | `math.exp(1) → 2.718281828459045` | библ. 9 |
| `math.log(x)` | натуральный логарифм; в документе: \|import("std/math") | `math.log(math.e) → 1.0` | библ. 9 |
| `math.log10(x)` | десятичный логарифм; в документе: \|import("std/math") | `math.log10(1000) → 3.0` | библ. 9 |
| `math.sin(x)` | синус (радианы); в документе: \|import("std/math") | `math.sin(math.pi / 2) → 1.0` | библ. 9 |
| `math.cos(x)` | косинус (радианы); в документе: \|import("std/math") | `math.cos(0) → 1.0` | библ. 9 |
| `math.tan(x)` | тангенс (радианы); в документе: \|import("std/math") | `math.tan(0) → 0.0` | библ. 9 |
| `math.atan2(y, x)` | угол точки (x, y), радианы; в документе: \|import("std/math") | `math.atan2(1, 1) → 0.7853981633974483` | библ. 9 |
| `math.floor(x)` | округлить вниз до целого (decimal); в документе: \|import("std/math") | `math.floor(-2.5) → -3` | библ. 9 |
| `math.ceil(x)` | округлить вверх до целого (decimal); в документе: \|import("std/math") | `math.ceil(2.1) → 3` | библ. 9 |
| `math.pi` | число π (float); в документе: \|import("std/math") | `math.pi → 3.141592653589793` | библ. 9 |
| `math.e` | число e (float); в документе: \|import("std/math") | `math.e → 2.718281828459045` | библ. 9 |

## QR-коды и кодировки

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `qr_matrix(data, ecc="M", min_version=1, max_version=40, encoding="utf-8")` | QR-код текста (байтовый режим): {version, ecc, mask, size, rows} | `qr_matrix("https://primula.example").version → 2` | библ. 10 |
| `qr_svg(data, ecc="M", min_version=1, max_version=40, encoding="utf-8", size="30mm", quiet=4, circle=0)` | QR-код как SVG для \|img(svg=…); circle= оставляет белый круг в центре | `len(qr_svg("https://primula.example")) > 0 → True` | библ. 10 |
| `base64url(text, encoding="utf-8")` | Base64URL байтов текста, без дополнения = | `base64url("Київ") → "0JrQuNGX0LI"` | библ. 10 |

## Проверки и документ

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `fail(*message)` | остановить сборку с ошибкой в этом месте | `fail("no price")` | 12.9 |
| `debug(*values)` | записать значения в отчёт сборки, а не в документ | `debug(total)` | 12.9 |
| `has(feature)` | есть ли у варианта изделия функция (keys: проекта, --feature) | `has("wifi")` | 9.2 |
| `markup(text)` | разметка Primula из строки (content) | `markup("\|*{" + name + "}")` | 4.2 |
| `param(name, default)` | параметр документа по имени (и в модуле: его настройки), или значение по умолчанию (решение 144) | `param("currency", "UAH")` | 10.6 |
| `collect(name, value)` | добавить значение в накопитель документа; результат — пустое содержимое (решение 143) | `\|(collect("cited", key))` | 4.6 |
| `collected(name)` | значения накопителя после всего документа, в порядке collect(); документ вычисляется дважды, в первом проходе [] (решение 143) | `collected("cited")` | 4.6 |
| `img(path, svg, **options)` | значение-изображение для watermark=, \|img(значение), \|figure(значение); путь или svg= | `img("assets/stamp.png")` | 8.6 |
| `col(width, id, type, **props)` | столбец таблицы: col(width, id=…, type=…, align=…) | `col("20mm..35mm", id="sum", type="money", align="right")` | 6.3 |
| `track(id, lang, title, **props)` | поток \|parallel: track(id, lang=…, title=…, width=…, primary=…) | `track("note", title="Коментар", width="28%", numbered=False, optional=True)` | 7.7 |

## Формулы таблиц

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `this_row(c)` | значение в столбце c текущей строки | `this_row("qty") * this_row("price")` | 6.8 |
| `cell(r, c)` | значение ячейки | `cell(2, "sum")` | 6.8 |
| `column(c, rows)` | список значений столбца (строки тела или rows=) | `sum(column("sum"))` | 6.8 |
| `body_rows()` | номера строк между заголовком и итогами | `body_rows()` | 6.8 |
| `avg(seq)` | среднее значение списка | `avg(column("qty"))` | 6.8 |
| `count(seq)` | количество непустых значений | `count(column("qty"))` | 6.8 |

## Код стилей

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `paragraph_style(name, parent, **props)` | определить абзацный стиль: имя, parent=…, свойства (11.3) | `paragraph_style("MyStyle", parent="…")` | 11.2 |
| `character_style(name, parent, **props)` | определить символьный стиль: имя, parent=…, свойства (11.3) | `character_style("MyStyle", parent="…")` | 11.2 |
| `block_style(name, parent, **props)` | определить блочный стиль: имя, parent=…, свойства (11.3) | `block_style("MyStyle", parent="…")` | 11.2 |
| `table_style(name, parent, **props)` | определить табличный стиль: имя, parent=…, свойства (11.3) | `table_style("MyStyle", parent="…")` | 11.2 |
| `list_style(name, parent, **props)` | определить списочный стиль: имя, parent=…, свойства (11.3) | `list_style("MyStyle", parent="…")` | 11.2 |
| `frame_style(name, parent, **props)` | определить фреймовый стиль: имя, parent=…, свойства (11.3) | `frame_style("MyStyle", parent="…")` | 11.2 |
| `page_style(name, parent, **props)` | определить страничный стиль: имя, parent=…, свойства (11.3) | `page_style("MyStyle", parent="…")` | 11.2 |
| `derive(base, name, **props)` | производный стиль: его детерминированное имя для \|.(…) | `derive("Clause", left="10mm")` | 11.4 |
| `structure_styles()` | стили конструкций структуры: paragraph=, heading=, clause=… | `structure_styles(paragraph="Body")` | 11.5 |
| `structure_profile()` | профиль структуры: "business" или "report" | `structure_profile("business")` | 5.1 |
| `numbering(headings, heading_format, clause_format, figures, tables, ref_format)` | нумерация заголовков, пунктов, рисунков и таблиц | `numbering(figures="by_chapter")` | 5.2 |
| `captions(lang, figure, table)` | слова подписей рисунков и таблиц | `captions("uk", figure="Рисунок", table="Таблиця")` | 5.8 |
| `appendices(lang, designation, numbering, letters, page_break, toc, title_format)` | обозначение и оформление приложений | `appendices("uk", designation="ДОДАТОК")` | 5.9 |
| `ref_labels(lang)` | слова ссылок \|@(id, "label") | `ref_labels("uk", clause="п.")` | 5.7 |
| `footnotes(numbering, restart, format, separator)` | нумерация и разделитель сносок | `footnotes(restart="page")` | 5.10 |
| `abbreviations(first, sort)` | первое употребление и сортировка сокращений | `abbreviations(first="expand")` | 9.4 |
| `typography(percent_space, nbsp_short, nbsp_words)` | типографика: percent_space, nbsp_short, nbsp_words | `typography(nbsp_short=True)` | библ. 7 |
| `admonition_symbols(danger, warning, caution, notice, note, tip)` | изображения знаков безопасности предупреждений | `admonition_symbols(danger="assets/signs/w012.svg")` | 9.1 |
| `admonition_words(lang, danger, warning, caution, notice, note, tip, notes)` | сигнальные слова предупреждений | `admonition_words("uk", danger="НЕБЕЗПЕКА")` | 9.1 |
| `review_marks(lang, true, false, watermark)` | тексты пометок и водяного знака --review | `review_marks("uk", watermark="НЕ ДЛЯ ВИПУСКУ")` | 9.2 |
| `watermark()` | водяной знак на стилях страниц | `watermark("ПРОЄКТ")` | 8.6 |
| `header()` | верхний колонтитул стиля страницы | `header("Portrait", markup("…"))` | 7.6 |
| `footer()` | нижний колонтитул стиля страницы | `footer("Portrait", markup("…"))` | 7.6 |
| `placeholders()` | заполнители \|?{…}: "mark" (черновик) или "final" | `placeholders("final")` | 4.2 |
| `quotes()` | кавычки языка для \|"{…} | `quotes("de", ("„", "“"), ("‚", "‘"))` | 4.2 |
| `currency(code, lang, short, units, frac, gender, minor, minor_gender, minor_digits)` | добавить или изменить валюту библиотеки | `currency("PLN", "uk", short="zł")` | библ. 1 |
| `unit(unit, lang, symbol, quantity, factor, offset)` | добавить или изменить единицу библиотеки | `unit("rpm", "uk", symbol="об/хв", quantity="frequency", factor=1/60)` | библ. 1 |
| `month_names(lang, nom, gen, loc)` | названия месяцев языка | `month_names("uk", gen=["січня", …])` | библ. 1 |

## Проект

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `build(source, output, params, keys, pdf)` | зарегистрировать цель сборки проекта | `build("act.prml", params=row, output=f"out/act-{row.no}.odt")` | 10.7 |
| `batch_mode()` | True во время сборки всего проекта | `batch_mode()` | 10.6 |

## Методы

| Вызов | Назначение | Пример → результат | § |
| --- | --- | --- | --- |
| `str.split(sep=None, maxsplit=-1)` | разбить по разделителю (без него — по пробелам) | `"a, b".split(", ") → ['a', 'b']` | 12.10 |
| `str.rsplit(sep=None, maxsplit=-1)` | разбить справа | `"a.b.c".rsplit(".", 1) → ['a.b', 'c']` | 12.10 |
| `str.splitlines(keepends=False)` | список строк | `"a\nb".splitlines() → ['a', 'b']` | 12.10 |
| `str.join(items)` | соединить строки этой строкой | `", ".join(["a", "b"]) → "a, b"` | 12.10 |
| `str.strip(chars=None)` | без пробелов (или символов) с обоих концов | `"  a ".strip() → "a"` | 12.10 |
| `str.lstrip(chars=None)` | без пробелов в начале | `"  a".lstrip() → "a"` | 12.10 |
| `str.rstrip(chars=None)` | без пробелов в конце | `"a  ".rstrip() → "a"` | 12.10 |
| `str.replace(old, new, count=-1)` | заменить подстроку | `"a-b".replace("-", "/") → "a/b"` | 12.10 |
| `str.startswith(prefix)` | начинается ли с префикса | `"ДСТУ 3008".startswith("ДСТУ") → True` | 12.10 |
| `str.endswith(suffix)` | заканчивается ли суффиксом | `"act.prml".endswith(".prml") → True` | 12.10 |
| `str.find(sub, start=None, end=None)` | индекс подстроки или −1 | `"abc".find("c") → 2` | 12.10 |
| `str.rfind(sub, start=None, end=None)` | индекс последнего вхождения или −1 | `"abca".rfind("a") → 3` | 12.10 |
| `str.count(sub, start=None, end=None)` | количество вхождений | `"banana".count("a") → 3` | 12.10 |
| `str.upper()` | заглавными буквами | `"київ".upper() → "КИЇВ"` | 12.10 |
| `str.lower()` | строчными буквами | `"КИЇВ".lower() → "київ"` | 12.10 |
| `str.capitalize()` | первая заглавная, остальные строчные | `"кИЇВ".capitalize() → "Київ"` | 12.10 |
| `str.title()` | каждое слово с заглавной | `"нова пошта".title() → "Нова Пошта"` | 12.10 |
| `str.isdigit()` | только ли цифры | `"2026".isdigit() → True` | 12.10 |
| `str.isalpha()` | только ли буквы | `"Київ".isalpha() → True` | 12.10 |
| `str.isspace()` | только ли пробелы | `" ".isspace() → True` | 12.10 |
| `str.zfill(width)` | дополнить нулями слева | `"7".zfill(3) → "007"` | 12.10 |
| `str.format(*args, **kwargs)` | подставить значения: "{0} — {name}" | `"{0} шт.".format(3) → "3 шт."` | 12.10 |
| `list.append(x)` | добавить элемент (внутри функций) | `[1].append(2)` | 12.10 |
| `list.extend(seq)` | добавить элементы списка | `[1].extend([2, 3])` | 12.10 |
| `list.insert(i, x)` | вставить элемент по индексу | `[1].insert(0, 0)` | 12.10 |
| `list.pop(i=-1)` | удалить и вернуть элемент (последний) | `[1, 2].pop() → 2` | 12.10 |
| `list.remove(x)` | удалить первый равный элемент | `[1, 2].remove(1)` | 12.10 |
| `list.index(x)` | индекс элемента | `["a", "b"].index("b") → 1` | 12.10 |
| `list.count(x)` | количество равных элементов | `[1, 1, 2].count(1) → 2` | 12.10 |
| `list.sort(key, reverse=False)` | отсортировать на месте | `[2, 1].sort()` | 12.10 |
| `list.reverse()` | обратить на месте | `[1, 2].reverse()` | 12.10 |
| `dict.get(key, default=None)` | значение по ключу или по умолчанию | `{"a": 1}.get("b", 0) → 0` | 12.10 |
| `dict.keys()` | список ключей | `{"a": 1}.keys() → ['a']` | 12.10 |
| `dict.values()` | список значений | `{"a": 1}.values() → [1]` | 12.10 |
| `dict.items()` | пары (ключ, значение) | `{"a": 1}.items() → [('a', 1)]` | 12.10 |
| `dict.update(other)` | добавить пары другого словаря | `{"a": 1}.update({"b": 2})` | 12.10 |
| `dict.pop(key, default)` | удалить ключ и вернуть значение | `{"a": 1}.pop("a") → 1` | 12.10 |
| `dict.setdefault(key, default=None)` | значение по ключу; отсутствует — установить по умолчанию | `{}.setdefault("a", 1) → 1` | 12.10 |
