"""Spreadsheet data: ``load_ods`` and ``load_xlsx`` (10.5, decision 138).

Both formats are ZIP archives of XML parts, read with the standard library:

* ODS (OpenDocument spreadsheet, ODF 1.3): ``content.xml`` — tables, rows
  and cells with ``office:value-type`` and the typed value attributes;
  repeated rows and columns (``table:number-rows-repeated``,
  ``table:number-columns-repeated``) are expanded only up to the last
  non-empty cell.
* XLSX (Office Open XML, ECMA-376): ``xl/workbook.xml`` (sheet names, the
  1904 date system), ``xl/_rels/workbook.xml.rels`` (sheet parts),
  ``xl/sharedStrings.xml``, ``xl/styles.xml`` (number formats tell dates
  from numbers) and ``xl/worksheets/sheet*.xml``.

The value of a formula cell is the result saved in the file by the program
that wrote it (LibreOffice and Excel save it); a formula without a saved
result is an error — the file must be saved by a spreadsheet program.  The
translator never computes formulas, so the result does not depend on the
machine (10.5).

Values: a number is a ``decimal`` rounded to 15 significant digits (the
precision of spreadsheet programs: 0.1 + 0.2 saved as 0.30000000000000004
is 0.3); a date or a date-time cell is a ``datetime``; a boolean is a
``bool``; text is a string (paragraphs of a cell joined by a line feed); an
empty cell is ``None``; an error value (``#DIV/0!``, ``Err:502``) is an
error that names the sheet and the cell.

Arguments: ``sheet`` — a name or a number from 1 (default: the first
sheet); ``range`` — ``"A1:D20"`` or a start cell ``"A3"`` (to the end of
the used area); ``header`` — the first row of the range gives the field
names (default), ``False`` names the fields by column letters (``A``,
``B``…); ``types`` — as in ``load_csv``.  Rows whose cells are all empty
are skipped.

Safety: an archive whose parts would unpack to more than
:data:`MAX_UNPACKED` bytes, a part with a ``DOCTYPE`` (entity expansion)
and a broken archive are errors; the cells count against the collection
limit of the evaluation.
"""

from __future__ import annotations

import datetime as _dt
import re
import zipfile
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any, Callable, Iterator
from xml.etree import ElementTree

from primula.core.errors import CoreError, core_error
from primula.core.values import DateTime, DateTimeError, PList, Record, digits_ok, freeze
from primula.unicode import nfkc

#: Unpacked size limit of the XML parts read from one file (zip bombs).
MAX_UNPACKED = 200 * 1024 * 1024
#: Significant digits kept from a binary number of a spreadsheet.
NUMBER_DIGITS = 15

_NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "calcext": "urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0",
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
_CELL_RE = re.compile(r"^([A-Za-z]{1,3})([1-9][0-9]{0,6})$")


class SheetError(Exception):
    """A problem of the file or a cell; ``where`` names the sheet and the cell."""

    def __init__(self, problem: str, where: str = "") -> None:
        super().__init__(problem)
        self.problem = problem
        self.where = where


class ErrorValue:
    """An error value of a cell (``#DIV/0!``): reported when the cell is read."""

    def __init__(self, text: str) -> None:
        self.text = text


# --- cell references ------------------------------------------------------------------------------

def column_letters(index: int) -> str:
    """``0`` -> ``A``, ``25`` -> ``Z``, ``26`` -> ``AA``."""
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def column_index(letters: str) -> int:
    """``A`` -> ``0``, ``AA`` -> ``26``."""
    index = 0
    for char in letters.upper():
        index = index * 26 + ord(char) - 64
    return index - 1


def parse_cell(text: str) -> tuple[int, int]:
    """``"B7"`` -> (row 6, column 1), 0-based."""
    match = _CELL_RE.match(text.strip())
    if not match:
        raise ValueError(text)
    return int(match.group(2)) - 1, column_index(match.group(1))


def parse_range(text: str) -> tuple[tuple[int, int], tuple[int, int] | None]:
    """``"A1:D20"`` or ``"A3"`` -> (start, end or ``None``)."""
    parts = text.split(":")
    if len(parts) == 1:
        return parse_cell(parts[0]), None
    if len(parts) == 2:
        start, end = parse_cell(parts[0]), parse_cell(parts[1])
        if end[0] < start[0] or end[1] < start[1]:
            raise ValueError(text)
        return start, end
    raise ValueError(text)


# --- the archive ------------------------------------------------------------------------------------

class _Archive:
    """Parts of a ZIP file, with the limit of the unpacked size."""

    def __init__(self, data: bytes) -> None:
        try:
            self.zip = zipfile.ZipFile(BytesIO(data))
        except zipfile.BadZipFile:
            raise SheetError("not a ZIP archive (ODS and XLSX files are ZIP archives)") from None
        self.unpacked = 0

    def has(self, name: str) -> bool:
        return name in self.zip.namelist()

    def xml(self, name: str) -> ElementTree.Element:
        try:
            info = self.zip.getinfo(name)
        except KeyError:
            raise SheetError(f"the part '{name}' is missing") from None
        self.unpacked += info.file_size
        if self.unpacked > MAX_UNPACKED:
            raise SheetError(f"the file unpacks to more than {MAX_UNPACKED // (1024 * 1024)} MB")
        try:
            data = self.zip.read(name)
        except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
            raise SheetError(f"cannot unpack '{name}': {exc}") from None
        if b"<!DOCTYPE" in data[:4096] or b"<!ENTITY" in data:
            raise SheetError(f"the part '{name}' has a DOCTYPE or ENTITY declaration")
        try:
            return ElementTree.fromstring(data)
        except ElementTree.ParseError as exc:
            raise SheetError(f"invalid XML in '{name}': {exc}") from None


def _q(prefix: str, name: str) -> str:
    return f"{{{_NS[prefix]}}}{name}"


# --- numbers and dates ----------------------------------------------------------------------------

def number(text: str) -> Any:
    """A saved number as a ``decimal`` of at most 15 significant digits; integers keep scale 0."""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError(text) from None
    if not value.is_finite():
        raise ValueError(text)
    if value.is_zero():
        return 0
    rounded = Decimal(format(value, f".{NUMBER_DIGITS}g")) if value.adjusted() < 64 else value
    if rounded == rounded.to_integral_value():
        return int(rounded)
    rounded = rounded.normalize()
    if not digits_ok(rounded):
        raise ValueError(text)
    return rounded


def iso_moment(text: str) -> DateTime:
    """``2026-10-12`` or ``2026-10-12T14:30:00[.ms]`` of ODS (seconds kept, fraction dropped)."""
    text = text.strip()
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?)?", text)
    if not match:
        raise ValueError(text)
    year, month, day, hour, minute, second = match.groups()
    return DateTime.of(int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0))


def serial_moment(serial: Decimal, date1904: bool) -> DateTime:
    """A spreadsheet serial number (days) as a ``datetime``, rounded to the second.

    The 1900 system counts from 1899-12-30 for serial numbers from 61 on
    (Excel keeps the nonexistent 29 February 1900 as 60); the 1904 system
    counts from 1904-01-01.
    """
    if date1904:
        epoch = _dt.datetime(1904, 1, 1)
    elif serial < 61:
        epoch = _dt.datetime(1899, 12, 31)
        if serial >= 60:
            raise ValueError("29.02.1900 does not exist")
    else:
        epoch = _dt.datetime(1899, 12, 30)
    seconds = int((serial * 86400).to_integral_value())
    moment = epoch + _dt.timedelta(seconds=seconds)
    return DateTime.of(moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second)


# --- ODS -------------------------------------------------------------------------------------------

def _ods_text(element: ElementTree.Element) -> str:
    """Text of a cell: paragraphs joined by line feeds; spaces, tabs and breaks of ODF text."""
    paragraphs = []
    for paragraph in element:
        if paragraph.tag not in (_q("text", "p"), _q("text", "h")):
            continue
        parts: list[str] = []

        def walk(node: ElementTree.Element) -> None:
            if node.text:
                parts.append(node.text)
            for child in node:
                if child.tag == _q("text", "s"):
                    parts.append(" " * int(child.get(_q("text", "c"), "1")))
                elif child.tag == _q("text", "tab"):
                    parts.append("\t")
                elif child.tag == _q("text", "line-break"):
                    parts.append("\n")
                elif child.tag != _q("office", "annotation"):
                    walk(child)
                if child.tail:
                    parts.append(child.tail)

        walk(paragraph)
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def _ods_value(cell: ElementTree.Element) -> Any:
    if cell.get(_q("calcext", "value-type")) == "error":
        # LibreOffice saves an error result as an empty string with the error text in the paragraph.
        return ErrorValue(_ods_text(cell) or "error")
    kind = cell.get(_q("office", "value-type"))
    if kind is None:
        text = _ods_text(cell)
        if cell.get(_q("table", "formula")) is not None and not text:
            raise SheetError("the formula has no saved result: open and save the file in a spreadsheet program")
        if text.startswith(("Err:", "#")) and cell.get(_q("table", "formula")) is not None:
            return ErrorValue(text)
        return text or None
    if kind in ("float", "percentage", "currency"):
        return number(cell.get(_q("office", "value"), ""))
    if kind == "date":
        return iso_moment(cell.get(_q("office", "date-value"), ""))
    if kind == "time":
        # A duration PT14H30M00S: a time of the day without a date.
        match = re.fullmatch(r"-?PT?(\d+)H(\d+)M(\d+)(?:\.\d+)?S", cell.get(_q("office", "time-value"), ""))
        if not match:
            raise ValueError("time")
        hours, minutes, seconds = (int(x) for x in match.groups())
        return _time_text(hours, minutes, seconds)
    if kind == "boolean":
        return cell.get(_q("office", "boolean-value"), "false") == "true"
    if kind == "string":
        value = cell.get(_q("office", "string-value"))
        text = value if value else _ods_text(cell)
        if cell.get(_q("table", "formula")) is not None and text.startswith(("Err:", "#")):
            return ErrorValue(text)
        return text
    raise SheetError(f"unknown cell type '{kind}'")


def _time_text(hours: int, minutes: int, seconds: int) -> str:
    """A time cell without a date is kept as text ``HH:MM:SS`` (``datetime`` needs a date)."""
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _ods_rows(archive: _Archive, sheet: Any, meter: Callable[[int], None]) -> tuple[str, dict[tuple[int, int], Any]]:
    root = archive.xml("content.xml")
    body = root.find(_q("office", "body"))
    spreadsheet = body.find(_q("office", "spreadsheet")) if body is not None else None
    if spreadsheet is None:
        raise SheetError("the file is not an OpenDocument spreadsheet")
    tables = spreadsheet.findall(_q("table", "table"))
    table, name = _pick(tables, [t.get(_q("table", "name"), "") for t in tables], sheet)
    cells: dict[tuple[int, int], Any] = {}
    row_index = 0
    for row in _ods_row_elements(table):
        repeat = int(row.get(_q("table", "number-rows-repeated"), "1"))
        row_cells: dict[int, Any] = {}
        column = 0
        for cell in row:
            if cell.tag not in (_q("table", "table-cell"), _q("table", "covered-table-cell")):
                continue
            span = int(cell.get(_q("table", "number-columns-repeated"), "1"))
            try:
                value = _ods_value(cell) if cell.tag == _q("table", "table-cell") else None
            except (ValueError, DateTimeError):
                raise SheetError("the saved value cannot be read", f"{name}!{column_letters(column)}{row_index + 1}") \
                    from None
            except SheetError as exc:
                raise SheetError(exc.problem, f"{name}!{column_letters(column)}{row_index + 1}") from None
            if value is not None:
                for k in range(span):
                    row_cells[column + k] = value
                meter(span)
            column += span
        if row_cells:
            for k in range(repeat):
                for c, value in row_cells.items():
                    cells[(row_index + k, c)] = value
                meter(len(row_cells))
        row_index += repeat
    return name, cells


def _ods_row_elements(table: ElementTree.Element) -> Iterator[ElementTree.Element]:
    """Rows of a table, also inside row groups and header rows."""
    for child in table:
        if child.tag == _q("table", "table-row"):
            yield child
        elif child.tag in (_q("table", "table-row-group"), _q("table", "table-header-rows"),
                           _q("table", "table-rows")):
            yield from _ods_row_elements(child)


# --- XLSX ------------------------------------------------------------------------------------------

#: Built-in number formats of dates and times (ECMA-376, 18.8.30).
_XLSX_DATE_FORMATS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 27, 30, 36, 45, 46, 47, 50, 57}


def _is_date_format(code: str) -> bool:
    """A custom number format shows a date or a time (``dd.mm.yyyy``, ``h:mm``), not ``[Red]0.00``."""
    text = re.sub(r'"[^"]*"|\\.|\[[^\]]*\]', "", code)
    return re.search(r"[dmyhs]", text, re.IGNORECASE) is not None and "General" not in text


def _xlsx_rows(archive: _Archive, sheet: Any, meter: Callable[[int], None]
               ) -> tuple[str, dict[tuple[int, int], Any]]:
    workbook = archive.xml("xl/workbook.xml")
    properties = workbook.find(_q("main", "workbookPr"))
    date1904 = properties is not None and properties.get("date1904", "false") in ("1", "true")
    sheets = workbook.find(_q("main", "sheets"))
    entries = list(sheets) if sheets is not None else []
    entry, name = _pick(entries, [e.get("name", "") for e in entries], sheet)
    relations = archive.xml("xl/_rels/workbook.xml.rels")
    target = None
    for relation in relations:
        if relation.get("Id") == entry.get(_q("rel", "id")):
            target = relation.get("Target", "")
    if not target:
        raise SheetError(f"the part of the sheet '{name}' is not found")
    part = target.lstrip("/") if target.startswith("/") else "xl/" + target
    strings = _xlsx_shared_strings(archive)
    dates = _xlsx_date_styles(archive)
    root = archive.xml(part)
    data = root.find(_q("main", "sheetData"))
    cells: dict[tuple[int, int], Any] = {}
    if data is None:
        return name, cells
    next_row = 0
    for row in data.findall(_q("main", "row")):
        row_index = int(row.get("r", next_row + 1)) - 1
        next_row = row_index + 1
        next_column = 0
        for cell in row.findall(_q("main", "c")):
            reference = cell.get("r")
            if reference:
                _, column = parse_cell(reference)
            else:
                column = next_column
            next_column = column + 1
            where = f"{name}!{column_letters(column)}{row_index + 1}"
            try:
                value = _xlsx_value(cell, strings, dates, date1904)
            except (ValueError, DateTimeError, IndexError):
                raise SheetError("the saved value cannot be read", where) from None
            except SheetError as exc:
                raise SheetError(exc.problem, where) from None
            if value is not None:
                cells[(row_index, column)] = value
                meter(1)
    return name, cells


def _xlsx_shared_strings(archive: _Archive) -> list[str]:
    if not archive.has("xl/sharedStrings.xml"):
        return []
    return [_xlsx_text(item) for item in archive.xml("xl/sharedStrings.xml").findall(_q("main", "si"))]


def _xlsx_text(item: ElementTree.Element) -> str:
    """Text of a string item: ``<t>`` or rich-text runs ``<r><t>``; phonetic runs are skipped."""
    parts = []
    for child in item:
        if child.tag == _q("main", "t"):
            parts.append(child.text or "")
        elif child.tag == _q("main", "r"):
            for t in child.findall(_q("main", "t")):
                parts.append(t.text or "")
    return "".join(parts)


def _xlsx_date_styles(archive: _Archive) -> set[int]:
    """Indexes of cell formats (``s=``) whose number format is a date or a time."""
    if not archive.has("xl/styles.xml"):
        return set()
    styles = archive.xml("xl/styles.xml")
    custom = {}
    formats = styles.find(_q("main", "numFmts"))
    if formats is not None:
        for item in formats.findall(_q("main", "numFmt")):
            custom[int(item.get("numFmtId", "0"))] = item.get("formatCode", "")
    result = set()
    xfs = styles.find(_q("main", "cellXfs"))
    for index, xf in enumerate(xfs.findall(_q("main", "xf")) if xfs is not None else []):
        format_id = int(xf.get("numFmtId", "0"))
        if format_id in _XLSX_DATE_FORMATS or (format_id in custom and _is_date_format(custom[format_id])):
            result.add(index)
    return result


def _xlsx_value(cell: ElementTree.Element, strings: list[str], dates: set[int], date1904: bool) -> Any:
    kind = cell.get("t", "n")
    value = cell.find(_q("main", "v"))
    text = value.text if value is not None else None
    if kind == "inlineStr":
        item = cell.find(_q("main", "is"))
        return _xlsx_text(item) if item is not None else None
    if text is None:
        if cell.find(_q("main", "f")) is not None:
            raise SheetError("the formula has no saved result: open and save the file in a spreadsheet program")
        return None
    if kind == "s":
        return strings[int(text)]
    if kind == "str":
        return text
    if kind == "b":
        return text.strip() == "1"
    if kind == "e":
        return ErrorValue(text)
    if kind == "d":
        return iso_moment(text[:19])
    serial = number(text)
    if int(cell.get("s", "0")) in dates:
        return serial_moment(Decimal(serial), date1904)
    return serial


# --- common ----------------------------------------------------------------------------------------

def _pick(items: list[Any], names: list[str], sheet: Any) -> tuple[Any, str]:
    if not items:
        raise SheetError("the file has no sheets")
    if sheet is None:
        return items[0], names[0]
    if isinstance(sheet, str):
        if sheet in names:
            index = names.index(sheet)
            return items[index], names[index]
        raise SheetError(f"no sheet '{sheet}'; the sheets: {', '.join(names)}")
    index = int(sheet)
    if not 1 <= index <= len(items):
        raise SheetError(f"no sheet {index}; the file has {len(items)}")
    return items[index - 1], names[index - 1]


def read(data: bytes, kind: str, sheet: Any, area: Any, header: bool, converters: dict[str, Callable[[Any], Any]],
         meter: Callable[[int], None]) -> PList:
    """Rows of a sheet as records (the common part of ``load_ods`` and ``load_xlsx``).

    Args:
        data: the bytes of the file.
        kind: ``ods`` or ``xlsx``.
        sheet: a name, a number from 1 or ``None``.
        area: ``"A1:D20"``, ``"A3"`` or ``None``.
        header: whether the first row gives the field names.
        converters: typed columns (field name -> converter of a cell value).
        meter: counts cells against the collection limit.

    Raises:
        SheetError: the file, the sheet, the range, a header or a cell is wrong.
    """
    archive = _Archive(data)
    name, cells = (_ods_rows if kind == "ods" else _xlsx_rows)(archive, sheet, meter)
    if area is None:
        start, end = (0, 0), None
    else:
        start, end = area
    if end is None:
        if not cells:
            return freeze(PList())
        end = (max(r for r, _ in cells), max(c for _, c in cells))
    rows_range = range(start[0], end[0] + 1)
    columns = list(range(start[1], end[1] + 1))
    if header:
        names = []
        for column in columns:
            value = cells.get((start[0], column))
            if isinstance(value, ErrorValue):
                raise SheetError(f"error value {value.text}", f"{name}!{column_letters(column)}{start[0] + 1}")
            names.append(nfkc(_plain(value).strip()) if value is not None else "")
        while names and not names[-1] and end[1] >= start[1] and area is None:
            names.pop()
            columns.pop()
        if any(not n for n in names) or len(set(names)) != len(names):
            raise SheetError("field names in the first row must be non-empty and unique", f"{name}!{start[0] + 1}")
        rows_range = range(start[0] + 1, end[0] + 1)
    else:
        names = [column_letters(column) for column in columns]
    for column in converters:
        if column not in names:
            raise SheetError(f"types: no column '{column}'")
    rows = PList()
    for r in rows_range:
        values = [cells.get((r, c)) for c in columns]
        if all(v is None for v in values):
            continue
        fields: dict[str, Any] = {}
        for column, field, value in zip(columns, names, values):
            where = f"{name}!{column_letters(column)}{r + 1}"
            if isinstance(value, ErrorValue):
                raise SheetError(f"error value {value.text}", where)
            converter = converters.get(field)
            if converter is not None:
                try:
                    value = converter(value)
                except (ValueError, DateTimeError):
                    raise SheetError(f"TYPE:{field}:{_plain(value)}", where) from None
            fields[field] = value
        rows.append(Record(fields))
    return freeze(rows)


def _plain(value: Any) -> str:
    """A cell value as text (field names, messages)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, DateTime):
        return str(value)
    return "" if value is None else str(value)
