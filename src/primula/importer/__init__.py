"""Import of documents of other formats into Primula (``primula import``, stage 19.3).

The source (DOCX, ODT, Markdown, HTML; the old ``.doc`` and ``.rtf`` through LibreOffice) is read by pandoc
into its document tree; :mod:`primula.importer.convert` writes Primula markup from the tree,
:mod:`primula.importer.reader` runs pandoc, :mod:`primula.importer.run` ties them together for the command.
The result is a draft for the author: the text, the structure, the tables, the images; the layout of the page
is not imported (``docs/dev/pandoc.md``).
"""
