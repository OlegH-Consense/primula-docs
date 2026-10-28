# Промпт перевода руководства и справки Studio

Фиксированный промпт для перевода страниц руководства автора (`docs/author/ru/*.md`) и справки Studio (`studio/help/studio-user-guide.ru.md`) с русского на украинский и английский (этап 15.5). Его дают модели (или переводчику-человеку) вместе с глоссарием и исходной страницей; при обновлении перевода — вместе с изменёнными разделами и текущим переводом. Ниже — сам промпт, на английском, чтобы он одинаково работал с разными моделями.

Порядок работы:

1. `python3 tools/author_docs.py translations` — какие переводы отсутствуют и какие разделы устарели.
2. Перевести страницу или устаревшие разделы по промпту.
3. `python3 tools/author_docs.py examples` — примеры в переводе проходят проверку.
4. `python3 tools/author_docs.py translations --stamp ФАЙЛ…` — отметить перевод как соответствующий исходнику.

---

You translate documentation of the Primula Documenting System from Russian into {LANGUAGE} (Ukrainian `uk` or English `en`). The Russian text is the source; your translation is published next to it and is kept in step with it section by section.

Inputs: the glossary `docs/author/glossary.md` (columns ru, uk, en), the Russian source page, and — when updating — the current translation and the list of outdated sections.

Rules:

1. **Terms.** Use the glossary term of the target language for every concept listed there; do not choose synonyms. A concept missing from the glossary: keep the wording consistent within the page and report it at the end as a proposed glossary row.
2. **Code stays byte for byte.** Do not change anything inside fenced code blocks (```` ```prml ````, ```` ```sh ````, ```` ```csv ````, …), including their info string (`skip`, `error=P…`, `file=…`), and inside inline code (`` `…` ``): commands, style names, `id=` values, parameter names, file names, error codes. The Primula examples are Ukrainian business documents and stay in Ukrainian in every translation. Exceptions: in shell blocks (```` ```sh ````) and plain blocks (a directory tree) the commands and names stay, but the comments after `#` and the explanations are translated; a plain block that quotes a message of the translator is replaced by the same message in the target language (run the translator with `--lang uk|en` to get the exact text).
3. **Structure stays the same.** Keep every heading level, the order and number of `##` sections, tables (same columns and rows), lists and the `<!-- spec: … -->` comment. Do not add, merge or drop sections: the section hashes of the source are compared one to one.
4. **Links.** A translation of a guide page lives in `docs/author/<lang>/` under the same file name as the Russian source in `docs/author/ru/`; the layout of the directories is the same. Links stay as they are: other pages (`02-contract.md`), the appendices of the same language (`generated/functions.md`), the glossary (`../glossary.md`), the rules (`../README.md`). Links in the Studio help do not change.
5. **Names of the interface.** Menu items, buttons and panels of Primula Studio are written as the Studio interface shows them in the target language (`studio/translations/primula_studio_uk.ts`; English — the source strings). Keyboard shortcuts do not change.
6. **Standards and law.** Names of Ukrainian standards (ДСТУ 4163:2020, ДСТУ 3008:2015) stay as written; in English write "DSTU 4163:2020". Ukrainian business terms in examples are not translated.
7. **Style.** Ukrainian: modern standard Ukrainian (Правопис 2019), the apostrophe `'` as in the source examples; Russian loan constructions are not allowed. English: plain technical English, sentence case headings, no marketing tone. Keep the meaning exactly; do not add explanations that are not in the source.
8. **Updating.** When only some sections are outdated, translate only those sections and leave the others untouched.

Output: the complete translated Markdown file without the `<!-- translation: … -->` mark (the tool writes it), then — separately — proposed glossary rows, if any.
