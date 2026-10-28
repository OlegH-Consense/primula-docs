# Contributing

Thank you for your interest in Primula.

## Issues

- **Bugs:** the smallest `.prml` file that shows the problem, the command you ran, the messages of the translator (`primula check FILE --lang en`), `primula --version`, the distribution and, for Studio, the Qt version (`primula-studio --runtime-info`).
- **Documents that do not come out right:** attach the source and the PDF, and describe what you expected.
- **Suggestions for the language:** describe the document you are writing and why the current markup is not enough; the specification is extended through numbered decisions (appendix 4.2 of the specification).

Do not attach documents with real personal data, requisites or signatures; replace them with obviously fictitious values.

## Changes

- Discuss larger changes in an issue first: the language, its specification and the translator change together.
- The translator is Python 3.11+ with the standard library and PyYAML only; Studio is C++20 with Qt 6.4+. Code comments are in English; the interface is translated into Ukrainian and Russian (`studio/translations/`).
- A change of the language comes with the specification (`primula-spec-v1.1-draft.ru.md`), the author guide (`docs/author/`, all three languages) and an example when it helps.
- Libraries of modules follow the scheme of the guide page [Libraries](docs/author/en/11-libraries.md) and keep their own test documents.
- The automated tests of the translator and Studio are kept in the development repository and run by the maintainer before each release; describe how you checked your change (the commands and the documents).

By submitting a contribution you agree that it is licensed under the licence of the files it changes ([LICENSING.md](LICENSING.md)).
