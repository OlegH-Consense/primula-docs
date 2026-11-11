# Додаток Б. Функції виразів

Згенеровано `tools/author_docs.py appendices` з довідника транслятора; не правити вручну.

## Числа

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `num(x, digits=None, lang)` | число за правилами мови: групи розрядів, кома | `num(12500, digits=2) → "12 500,00"` | бібл. 2 |
| `percent(x, digits=None, lang)` | відсоток з нерозривним пробілом: «20 %» | `percent(20) → "20 %"` | бібл. 2 |
| `round_to(x, step)` | округлити до кроку, половина від нуля | `round_to(1234, 50) → 1250` | бібл. 2 |
| `ceil_to(x, step)` | округлити до кроку вгору | `ceil_to(1201, 100) → 1300` | бібл. 2 |
| `floor_to(x, step)` | округлити до кроку вниз | `floor_to(1299, 100) → 1200` | бібл. 2 |
| `round_money(x)` | округлити до сотих, половина від нуля | `round_money(dec("10.005")) → 10.01` | бібл. 2 |
| `round(x, ndigits=None)` | округлити, половина від нуля; без ndigits — ціле | `round(2.675, 2) → 2.68` | 12.4 |
| `abs(x)` | модуль числа | `abs(-5) → 5` | 12.10 |
| `min(*values, key, default)` | найменше з аргументів або списку | `min(3, 1, 2) → 1` | 12.10 |
| `max(*values, key, default)` | найбільше з аргументів або списку | `max([3, 1, 2]) → 3` | 12.10 |
| `sum(seq, start=0)` | сума списку | `sum([1.50, 2.25]) → 3.75` | 12.10 |
| `dec(x)` | у decimal (з float — найкоротший десятковий запис) | `dec(0.1) → 0.1` | 12.4 |
| `float(x)` | у float; datetime дає серійне число | `float("2.5") → 2.5` | 12.4 |
| `int(x)` | відкинути дробову частину (decimal з масштабом 0) | `int(7.9) → 7` | 12.4 |

## Гроші й ПДВ

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `money(x, code, currency_style="short", lang)` | сума з валютою: «12 500,00 грн» | `money(12500, "UAH") → "12 500,00 грн"` | бібл. 3 |
| `money_words(x, code, kop="digits", cap=False, lang)` | сума прописом | `money_words(12500, "UAH") → "дванадцять тисяч п'ятсот гривень 00 копійок"` | бібл. 3 |
| `money_full(x, code, kop="digits", cap=False, currency_style="short", lang)` | сума цифрами і прописом у дужках (договірна форма) | `money_full(12500.50, "UAH") → "12 500,50 грн (дванадцять тисяч п'ятсот гривень 50 копійок)"` | бібл. 3 |
| `vat(x, rate)` | податок із суми без податку | `vat(1000, 20) → 200.00` | бібл. 3 |
| `with_vat(x, rate)` | сума з податком | `with_vat(1000, 20) → 1200.00` | бібл. 3 |
| `vat_in(x, rate)` | податок, що міститься в сумі з податком | `vat_in(1200, 20) → 200.00` | бібл. 3 |
| `without_vat(x, rate)` | сума без податку із суми з податком | `without_vat(1200, 20) → 1000.00` | бібл. 3 |
| `split(total, shares)` | поділити суму за частками; частини дають суму | `split(100, [1, 1, 1]) → [33.33, 33.33, 33.34]` | бібл. 3 |

## Прописом

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `words(x, code=None, gender="m", case="nom", lang)` | число прописом; words(x, "UAH") — сума | `words(21, gender="f") → "двадцять одна"` | бібл. 4 |
| `ordinal(n, gender="m", case="nom", lang)` | порядковий числівник прописом | `ordinal(21, case="gen") → "двадцять першого"` | бібл. 4 |
| `date_words(dt, lang)` | дата прописом | `date_words(date(2026, 10, 12)) → "дванадцятого жовтня дві тисячі двадцять шостого року"` | бібл. 4 |

## Дати й час

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `date(y, m, d)` | дата: date(y, m, d) або date("YYYY-MM-DD") | `date(2026, 10, 12) → date("2026-10-12")` | 12.3 |
| `datetime(y, m, d, h=0, mi=0, s=0)` | момент: datetime(y, m, d, h, mi, s), рядок ISO або серійне число | `datetime("2026-10-12T14:30") → datetime("2026-10-12T14:30:00")` | 12.3 |
| `build_date()` | дата початку збирання (--build-date, build_date: проєкту) | `build_date() → date("2026-10-12")` | 12.7 |
| `weeks(n)` | кількість діб у n тижнях: dt + weeks(2) | `weeks(2) → 14` | бібл. 5 |
| `hours(n)` | кількість діб у n годинах: dt + hours(36) | `hours(36) → 1.5` | бібл. 5 |
| `minutes(n)` | кількість діб у n хвилинах | `date(2026, 10, 12) + minutes(90) → datetime("2026-10-12T01:30:00")` | бібл. 5 |
| `add_months(dt, n)` | зсув на місяці (31 → останній день місяця) | `add_months(date(2026, 1, 31), 1) → date("2026-02-28")` | бібл. 5 |
| `add_years(dt, n)` | зсув на роки | `add_years(date(2028, 2, 29), 1) → date("2029-02-28")` | бібл. 5 |
| `fmt_date(dt, format="short", lang)` | дата текстом: short, long, contract або шаблон (ДСТУ 4163:2020) | `fmt_date(date(2026, 10, 12), "contract") → "«12» жовтня 2026 р."` | бібл. 5 |
| `fmt_time(dt, format="short", lang)` | час текстом: short або шаблон {hh}:{mi} | `fmt_time(datetime(2026, 10, 12, 14, 30, 0)) → "14:30"` | бібл. 5 |
| `fmt_datetime(dt, format="short", lang)` | дата й час текстом | `fmt_datetime(datetime(2026, 10, 12, 14, 30, 0), "long") → "12 жовтня 2026 року, 14:30"` | бібл. 5 |
| `weekday(dt, case="nom", lang)` | назва дня тижня (відмінок nom або acc) | `weekday(date(2026, 10, 12)) → "понеділок"` | бібл. 5 |
| `month_name(dt, case="nom", lang)` | назва місяця (відмінок nom, gen, loc) | `month_name(date(2026, 10, 12), case="gen") → "жовтня"` | бібл. 5 |
| `is_workday(dt, calendar)` | чи робочий день (за календарем проєкту) | `is_workday(date(2026, 10, 10)) → False` | бібл. 5 |
| `workdays(dt, n, calendar)` | дата через n робочих днів після dt (n < 0 — до) | `workdays(date(2026, 10, 9), 1) → date("2026-10-12")` | бібл. 5 |

## Одиниці й довжини

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `qty(x, unit, tol, digits=None, lang)` | значення з одиницею: «230 В», tol= — допуск | `qty(230, "V") → "230 В"` | бібл. 6 |
| `qty_range(low, high, unit, digits=None, lang)` | діапазон з одиницею: «100–240 В» | `qty_range(-20, 55, "degC") → "−20…+55 °C"` | бібл. 6 |
| `convert(x, from, to)` | перерахувати між одиницями однієї величини | `convert(1.5, "kW", "W") → 1500` | бібл. 6 |
| `length(text)` | довжина з рядка: length("10mm") | `length("10mm") + 5*mm → length("15mm")` | 12.3 |
| `mm` | константа довжини: 10*mm | `10*mm → length("10mm")` | 12.3 |
| `cm` | константа довжини: 10*cm | `10*cm → length("10cm")` | 12.3 |
| `pt` | константа довжини: 10*pt | `10*pt → length("10pt")` | 12.3 |
| `inch` | константа довжини: 10*inch | `10*inch → length("10inch")` | 12.3 |

## Текст

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `plural(n, *forms, frac, lang)` | форма слова за числом: plural(n, "день", "дні", "днів") | `plural(5, "день", "дні", "днів", lang="uk") → "днів"` | бібл. 7 |
| `join_list(items, last, sep=", ", lang)` | з'єднати список: «А, Б та В» | `join_list(["А", "Б", "В"], last="та") → "А, Б та В"` | бібл. 7 |
| `cap(s)` | велика перша літера | `cap("київ") → "Київ"` | бібл. 7 |
| `translit(s, lang)` | транслітерація (uk — постанова КМУ № 55, ru — ICAO Doc 9303) | `translit("Згорани", lang="uk") → "Zghorany"` | бібл. 7 |
| `sort_key(s, lang)` | ключ сортування за абеткою мови: sorted(names, key=sort_key) | `sorted(["Ґава", "Гора", "Єва", "Есе"], key=sort_key) → ['Гора', 'Ґава', 'Есе', 'Єва']` | бібл. 7 |
| `nbsp_short(s, lang)` | нерозривний пробіл після коротких прийменників і сполучників | `nbsp_short("в домі та у дворі", lang="uk") → "в домі та у дворі"` | бібл. 7 |
| `str(x)` | значення рядком (дати — ISO, числа — з крапкою) | `str(2.20) → "2.20"` | 12.10 |
| `repr(x)` | значення у вигляді коду | `repr("a") → "'a'"` | 12.10 |

## Списки й записи

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `len(seq)` | довжина: символи, елементи, ключі | `len("Київ") → 4` | 12.10 |
| `range(start, stop, step=1)` | числа від start до stop (не включно) з кроком | `range(1, 10, 3) → [1, 4, 7]` | 12.10 |
| `enumerate(seq, start=0)` | пари (номер, елемент) | `enumerate(["a", "b"], start=1) → [(1, 'a'), (2, 'b')]` | 12.10 |
| `zip(*lists)` | кортежі елементів з однаковим індексом | `zip([1, 2], ["a", "b"]) → [(1, 'a'), (2, 'b')]` | 12.10 |
| `sorted(seq, key, reverse=False)` | відсортований список | `sorted([3, 1, 2]) → [1, 2, 3]` | 12.10 |
| `reversed(seq)` | список у зворотному порядку | `reversed([1, 2, 3]) → [3, 2, 1]` | 12.10 |
| `any(seq)` | чи є хоч один істинний елемент | `any([0, 1]) → True` | 12.10 |
| `all(seq)` | чи всі елементи істинні | `all([1, 2]) → True` | 12.10 |
| `list(seq)` | список (з послідовності) | `list("abc") → ['a', 'b', 'c']` | 12.10 |
| `tuple(seq)` | кортеж | `tuple([1, 2]) → (1, 2)` | 12.10 |
| `dict(source=None, **items)` | словник: з пар, запису або key=value | `dict(a=1, b=2) → {'a': 1, 'b': 2}` | 12.10 |
| `record(source=None, **fields)` | запис з доступом через крапку: r.name | `record(name="Кабель", qty=3) → record(name='Кабель', qty=3)` | 12.6 |
| `bool(x)` | логічне значення | `bool("") → False` | 12.10 |
| `getattr(r, name, default)` | поле запису за ім'ям, зі значенням за замовчуванням | `getattr(record(a=1), "b", 0) → 0` | 12.6 |
| `hasattr(r, name)` | чи має запис поле | `hasattr(record(a=1), "a") → True` | 12.6 |
| `type(x)` | ім'я типу: "decimal", "str", "datetime"… | `type(1.5e3) → "float"` | 12.3 |

## Дані

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `group_by(items, key)` | словник «значення ключа → список записів» | `group_by([record(k="a", v=1), record(k="a", v=2)], "k") → {'a': [record(k='a', v=1), record(k='a', v=2)]}` | бібл. 8 |
| `sum_by(items, key, value)` | суми поля за групами | `sum_by([record(k="a", v=1), record(k="a", v=2)], "k", "v") → {'a': 3}` | бібл. 8 |
| `distinct(items, key)` | унікальні значення поля | `distinct([record(k="a"), record(k="b"), record(k="a")], "k") → ['a', 'b']` | бібл. 8 |
| `load_csv(path, types, sep)` | рядки файлу CSV як записи | `load_csv("data/items.csv")` | 10.5 |
| `load_yaml(path)` | дані файлу YAML (записи й списки) | `load_yaml("data/order.yaml")` | 10.5 |
| `load_json(path)` | дані файлу JSON | `load_json("data/order.json")` | 10.5 |
| `load_text(path)` | увесь текстовий файл як рядок (UTF-8; наприклад, SVG для \|img(svg=…)) | `load_text("img/sign.svg")` | 10.5 |
| `load_ods(path, sheet, range, header=True, types)` | рядки аркуша файлу ODS як записи (збережені результати формул) | `load_ods("data/items.ods", sheet="Позиції")` | 10.5 |
| `load_xlsx(path, sheet, range, header=True, types)` | рядки аркуша файлу XLSX як записи (збережені результати формул) | `load_xlsx("data/items.xlsx", sheet="Позиції")` | 10.5 |

## Математика (std/math)

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `math.sqrt(x)` | квадратний корінь; у документі: \|import("std/math") | `math.sqrt(2) → 1.4142135623730951` | бібл. 9 |
| `math.exp(x)` | e в степені x; у документі: \|import("std/math") | `math.exp(1) → 2.718281828459045` | бібл. 9 |
| `math.log(x)` | натуральний логарифм; у документі: \|import("std/math") | `math.log(math.e) → 1.0` | бібл. 9 |
| `math.log10(x)` | десятковий логарифм; у документі: \|import("std/math") | `math.log10(1000) → 3.0` | бібл. 9 |
| `math.sin(x)` | синус (радіани); у документі: \|import("std/math") | `math.sin(math.pi / 2) → 1.0` | бібл. 9 |
| `math.cos(x)` | косинус (радіани); у документі: \|import("std/math") | `math.cos(0) → 1.0` | бібл. 9 |
| `math.tan(x)` | тангенс (радіани); у документі: \|import("std/math") | `math.tan(0) → 0.0` | бібл. 9 |
| `math.atan2(y, x)` | кут точки (x, y), радіани; у документі: \|import("std/math") | `math.atan2(1, 1) → 0.7853981633974483` | бібл. 9 |
| `math.floor(x)` | округлити вниз до цілого (decimal); у документі: \|import("std/math") | `math.floor(-2.5) → -3` | бібл. 9 |
| `math.ceil(x)` | округлити вгору до цілого (decimal); у документі: \|import("std/math") | `math.ceil(2.1) → 3` | бібл. 9 |
| `math.pi` | число π (float); у документі: \|import("std/math") | `math.pi → 3.141592653589793` | бібл. 9 |
| `math.e` | число e (float); у документі: \|import("std/math") | `math.e → 2.718281828459045` | бібл. 9 |

## QR-коди й кодування

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `qr_matrix(data, ecc="M", min_version=1, max_version=40, encoding="utf-8")` | QR-код тексту (байтовий режим): {version, ecc, mask, size, rows} | `qr_matrix("https://primula.example").version → 2` | бібл. 10 |
| `qr_svg(data, ecc="M", min_version=1, max_version=40, encoding="utf-8", size="30mm", quiet=4, circle=0)` | QR-код як SVG для \|img(svg=…); circle= лишає біле коло в центрі | `len(qr_svg("https://primula.example")) > 0 → True` | бібл. 10 |
| `base64url(text, encoding="utf-8")` | Base64URL байтів тексту, без доповнення = | `base64url("Київ") → "0JrQuNGX0LI"` | бібл. 10 |

## Перевірки й документ

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `fail(*message)` | зупинити збирання з помилкою в цьому місці | `fail("no price")` | 12.9 |
| `debug(*values)` | записати значення у звіт збирання, а не в документ | `debug(total)` | 12.9 |
| `has(feature)` | чи має варіант виробу функцію (keys: проєкту, --feature) | `has("wifi")` | 9.2 |
| `markup(text)` | розмітка Primula з рядка (content) | `markup("\|*{" + name + "}")` | 4.2 |
| `param(name, default)` | параметр документа за назвою (і в модулі: його налаштування), або значення за замовчуванням (рішення 144) | `param("currency", "UAH")` | 10.6 |
| `collect(name, value)` | додати значення до накопичувача документа; результат — порожній вміст (рішення 143) | `\|(collect("cited", key))` | 4.6 |
| `collected(name)` | значення накопичувача після всього документа, у порядку collect(); документ обчислюється двічі, у першому проході [] (рішення 143) | `collected("cited")` | 4.6 |
| `img(path, svg, **options)` | значення-зображення для watermark=, \|img(значення), \|figure(значення); шлях або svg= | `img("assets/stamp.png")` | 8.6 |
| `col(width, id, type, **props)` | стовпець таблиці: col(width, id=…, type=…, align=…) | `col("20mm..35mm", id="sum", type="money", align="right")` | 6.3 |
| `track(id, lang, title, **props)` | потік \|parallel: track(id, lang=…, title=…, width=…, primary=…) | `track("note", title="Коментар", width="28%", numbered=False, optional=True)` | 7.7 |

## Формули таблиць

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `this_row(c)` | значення в стовпці c поточного рядка | `this_row("qty") * this_row("price")` | 6.8 |
| `cell(r, c)` | значення клітинки | `cell(2, "sum")` | 6.8 |
| `column(c, rows)` | список значень стовпця (рядки тіла або rows=) | `sum(column("sum"))` | 6.8 |
| `body_rows()` | номери рядків між заголовком і підсумками | `body_rows()` | 6.8 |
| `avg(seq)` | середнє значення списку | `avg(column("qty"))` | 6.8 |
| `count(seq)` | кількість непорожніх значень | `count(column("qty"))` | 6.8 |

## Код стилів

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `paragraph_style(name, parent, **props)` | визначити абзацний стиль: ім'я, parent=…, властивості (11.3) | `paragraph_style("MyStyle", parent="…")` | 11.2 |
| `character_style(name, parent, **props)` | визначити символьний стиль: ім'я, parent=…, властивості (11.3) | `character_style("MyStyle", parent="…")` | 11.2 |
| `block_style(name, parent, **props)` | визначити блоковий стиль: ім'я, parent=…, властивості (11.3) | `block_style("MyStyle", parent="…")` | 11.2 |
| `table_style(name, parent, **props)` | визначити табличний стиль: ім'я, parent=…, властивості (11.3) | `table_style("MyStyle", parent="…")` | 11.2 |
| `list_style(name, parent, **props)` | визначити списковий стиль: ім'я, parent=…, властивості (11.3) | `list_style("MyStyle", parent="…")` | 11.2 |
| `frame_style(name, parent, **props)` | визначити фреймовий стиль: ім'я, parent=…, властивості (11.3) | `frame_style("MyStyle", parent="…")` | 11.2 |
| `page_style(name, parent, **props)` | визначити сторінковий стиль: ім'я, parent=…, властивості (11.3) | `page_style("MyStyle", parent="…")` | 11.2 |
| `derive(base, name, **props)` | похідний стиль: його детерміноване ім'я для \|.(…) | `derive("Clause", left="10mm")` | 11.4 |
| `structure_styles()` | стилі конструкцій структури: paragraph=, heading=, clause=… | `structure_styles(paragraph="Body")` | 11.5 |
| `structure_profile()` | профіль структури: "business" або "report" | `structure_profile("business")` | 5.1 |
| `numbering(headings, heading_format, clause_format, figures, tables, ref_format)` | нумерація заголовків, пунктів, рисунків і таблиць | `numbering(figures="by_chapter")` | 5.2 |
| `captions(lang, figure, table)` | слова підписів рисунків і таблиць | `captions("uk", figure="Рисунок", table="Таблиця")` | 5.8 |
| `appendices(lang, designation, numbering, letters, page_break, toc, title_format)` | позначення й оформлення додатків | `appendices("uk", designation="ДОДАТОК")` | 5.9 |
| `ref_labels(lang)` | слова посилань \|@(id, "label") | `ref_labels("uk", clause="п.")` | 5.7 |
| `footnotes(numbering, restart, format, separator)` | нумерація й роздільник виносок | `footnotes(restart="page")` | 5.10 |
| `abbreviations(first, sort)` | перше вживання й сортування скорочень | `abbreviations(first="expand")` | 9.4 |
| `typography(percent_space, nbsp_short, nbsp_words)` | типографіка: percent_space, nbsp_short, nbsp_words | `typography(nbsp_short=True)` | бібл. 7 |
| `admonition_symbols(danger, warning, caution, notice, note, tip)` | зображення знаків безпеки попереджень | `admonition_symbols(danger="assets/signs/w012.svg")` | 9.1 |
| `admonition_words(lang, danger, warning, caution, notice, note, tip, notes)` | сигнальні слова попереджень | `admonition_words("uk", danger="НЕБЕЗПЕКА")` | 9.1 |
| `review_marks(lang, true, false, watermark)` | тексти позначок і водяного знака --review | `review_marks("uk", watermark="НЕ ДЛЯ ВИПУСКУ")` | 9.2 |
| `watermark()` | водяний знак на стилях сторінок | `watermark("ПРОЄКТ")` | 8.6 |
| `header()` | верхній колонтитул стилю сторінки | `header("Portrait", markup("…"))` | 7.6 |
| `footer()` | нижній колонтитул стилю сторінки | `footer("Portrait", markup("…"))` | 7.6 |
| `placeholders()` | заповнювачі \|?{…}: "mark" (чернетка) або "final" | `placeholders("final")` | 4.2 |
| `quotes()` | лапки мови для \|"{…} | `quotes("de", ("„", "“"), ("‚", "‘"))` | 4.2 |
| `currency(code, lang, short, units, frac, gender, minor, minor_gender, minor_digits)` | додати або змінити валюту бібліотеки | `currency("PLN", "uk", short="zł")` | бібл. 1 |
| `unit(unit, lang, symbol, quantity, factor, offset)` | додати або змінити одиницю бібліотеки | `unit("rpm", "uk", symbol="об/хв", quantity="frequency", factor=1/60)` | бібл. 1 |
| `month_names(lang, nom, gen, loc)` | назви місяців мови | `month_names("uk", gen=["січня", …])` | бібл. 1 |

## Проєкт

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `build(source, output, params, keys, pdf)` | зареєструвати ціль збирання проєкту | `build("act.prml", params=row, output=f"out/act-{row.no}.odt")` | 10.7 |
| `batch_mode()` | True під час збирання всього проєкту | `batch_mode()` | 10.6 |

## Методи

| Виклик | Призначення | Приклад → результат | § |
| --- | --- | --- | --- |
| `str.split(sep=None, maxsplit=-1)` | розбити за роздільником (без нього — за пробілами) | `"a, b".split(", ") → ['a', 'b']` | 12.10 |
| `str.rsplit(sep=None, maxsplit=-1)` | розбити справа | `"a.b.c".rsplit(".", 1) → ['a.b', 'c']` | 12.10 |
| `str.splitlines(keepends=False)` | список рядків | `"a\nb".splitlines() → ['a', 'b']` | 12.10 |
| `str.join(items)` | з'єднати рядки цим рядком | `", ".join(["a", "b"]) → "a, b"` | 12.10 |
| `str.strip(chars=None)` | без пробілів (або символів) з обох кінців | `"  a ".strip() → "a"` | 12.10 |
| `str.lstrip(chars=None)` | без пробілів на початку | `"  a".lstrip() → "a"` | 12.10 |
| `str.rstrip(chars=None)` | без пробілів у кінці | `"a  ".rstrip() → "a"` | 12.10 |
| `str.replace(old, new, count=-1)` | замінити підрядок | `"a-b".replace("-", "/") → "a/b"` | 12.10 |
| `str.startswith(prefix)` | чи починається з префікса | `"ДСТУ 3008".startswith("ДСТУ") → True` | 12.10 |
| `str.endswith(suffix)` | чи закінчується суфіксом | `"act.prml".endswith(".prml") → True` | 12.10 |
| `str.find(sub, start=None, end=None)` | індекс підрядка або −1 | `"abc".find("c") → 2` | 12.10 |
| `str.rfind(sub, start=None, end=None)` | індекс останнього входження або −1 | `"abca".rfind("a") → 3` | 12.10 |
| `str.count(sub, start=None, end=None)` | кількість входжень | `"banana".count("a") → 3` | 12.10 |
| `str.upper()` | великими літерами | `"київ".upper() → "КИЇВ"` | 12.10 |
| `str.lower()` | малими літерами | `"КИЇВ".lower() → "київ"` | 12.10 |
| `str.capitalize()` | перша велика, решта малі | `"кИЇВ".capitalize() → "Київ"` | 12.10 |
| `str.title()` | кожне слово з великої | `"нова пошта".title() → "Нова Пошта"` | 12.10 |
| `str.isdigit()` | чи лише цифри | `"2026".isdigit() → True` | 12.10 |
| `str.isalpha()` | чи лише літери | `"Київ".isalpha() → True` | 12.10 |
| `str.isspace()` | чи лише пробіли | `" ".isspace() → True` | 12.10 |
| `str.zfill(width)` | доповнити нулями зліва | `"7".zfill(3) → "007"` | 12.10 |
| `str.format(*args, **kwargs)` | підставити значення: "{0} — {name}" | `"{0} шт.".format(3) → "3 шт."` | 12.10 |
| `list.append(x)` | додати елемент (усередині функцій) | `[1].append(2)` | 12.10 |
| `list.extend(seq)` | додати елементи списку | `[1].extend([2, 3])` | 12.10 |
| `list.insert(i, x)` | вставити елемент за індексом | `[1].insert(0, 0)` | 12.10 |
| `list.pop(i=-1)` | вилучити й повернути елемент (останній) | `[1, 2].pop() → 2` | 12.10 |
| `list.remove(x)` | вилучити перший рівний елемент | `[1, 2].remove(1)` | 12.10 |
| `list.index(x)` | індекс елемента | `["a", "b"].index("b") → 1` | 12.10 |
| `list.count(x)` | кількість рівних елементів | `[1, 1, 2].count(1) → 2` | 12.10 |
| `list.sort(key, reverse=False)` | відсортувати на місці | `[2, 1].sort()` | 12.10 |
| `list.reverse()` | обернути на місці | `[1, 2].reverse()` | 12.10 |
| `dict.get(key, default=None)` | значення за ключем або типове | `{"a": 1}.get("b", 0) → 0` | 12.10 |
| `dict.keys()` | список ключів | `{"a": 1}.keys() → ['a']` | 12.10 |
| `dict.values()` | список значень | `{"a": 1}.values() → [1]` | 12.10 |
| `dict.items()` | пари (ключ, значення) | `{"a": 1}.items() → [('a', 1)]` | 12.10 |
| `dict.update(other)` | додати пари іншого словника | `{"a": 1}.update({"b": 2})` | 12.10 |
| `dict.pop(key, default)` | вилучити ключ і повернути значення | `{"a": 1}.pop("a") → 1` | 12.10 |
| `dict.setdefault(key, default=None)` | значення за ключем; відсутнє — встановити типове | `{}.setdefault("a", 1) → 1` | 12.10 |
