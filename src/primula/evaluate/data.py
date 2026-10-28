"""External data: ``load_yaml``, ``load_json``, ``load_csv``, ``load_ods``, ``load_xlsx``, ``load_text``
(10.5, 12.6, decisions 25, 51, 138, 140).

* Files are read only inside the project root, relative to the file whose
  code calls the function; they are read through the source manager, so
  their SHA-256 hashes appear in the build report (10.5, 14.3).
* YAML: the YAML 1.2 core schema with the Primula rules (decision 25),
  mappings become records.
* JSON: numbers with a point and no exponent are ``decimal``; ``NaN`` and
  ``Infinity`` are errors; duplicate keys are errors.
* CSV (decision 51): UTF-8 (BOM allowed), first line — field names,
  quoting by RFC 4180, separator ``,`` or ``;`` (detected from the first
  line, or ``sep=``); without ``types`` all values are strings; typed
  columns (10.5, v1.1): ``str``, ``decimal`` (an integer has scale 0),
  ``money`` (at most two digits after the separator), ``float``,
  ``datetime`` (``YYYY-MM-DD``, ``DD.MM.YYYY``, ``YYYY-MM-DDTHH:MM[:SS]``,
  ``DD.MM.YYYY HH:MM[:SS]``; a time zone is an error), ``bool``
  (``true``/``false``, ``1``/``0``).  Numbers: one decimal separator, ``.``
  or ``,``; digit groups only with a space or a no-break space; an empty
  cell of a typed column is ``None``.
* Field names (CSV columns, YAML and JSON keys) are normalised to NFKC;
  names that coincide after normalisation are an error (3.9).

* Text (decision 140): the whole file as one string — UTF-8, the BOM
  dropped, line ends LF, NFC, as every source; no parsing.  For SVG of
  ``|img(svg=…)``, text blocks kept outside the document and similar.
* ODS and XLSX (decision 138): :mod:`primula.evaluate.sheets` reads the
  saved values of a sheet; ``types`` as for CSV, converting cell values.

Errors point into the data file (line, column) with the call site as a
note-frame; errors of spreadsheet files name the sheet and the cell.
"""

from __future__ import annotations

import csv
import decimal
import io
import json
import re
from decimal import Decimal
from typing import Any, Callable

from primula import yamlio
from primula.i18n import Key
from primula.core.errors import CoreError, core_error, resolve
from primula.core.values import (
    Builtin, DateTime, DateTimeError, PList, Record, digits_ok, freeze, from_data, parse_iso_datetime,
)
from primula.diagnostics import error
from primula.evaluate import sheets
from primula.evaluate.loader import Loader
from primula.source import SourceFile, Span
from primula.unicode import nfkc

#: Column types of ``load_csv`` (10.5; ``int`` and ``date`` of v1.0 are gone).
CSV_TYPES = ("str", "decimal", "money", "float", "datetime", "bool")
#: Types of version 1.0 and their replacements (hint of the error).
_OLD_TYPES = {"int": "decimal", "date": "datetime"}

_GROUP_SPACES = (" ", " ", " ")
_INT_RE = re.compile(r"^[+-]?\d+$")
_NUMBER_RE = re.compile(r"^[+-]?(\d+([.,]\d*)?|[.,]\d+)$")


def make_data_builtins(loader: Loader) -> dict[str, Builtin]:
    """Built-in functions ``load_yaml``, ``load_json``, ``load_csv`` bound to a loader."""

    def base_and_span(span: Any) -> tuple[SourceFile, Span]:
        real = resolve(span)
        return real.source, real

    def load_yaml(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
        path = _path_argument("load_yaml", args, kwargs, span, ())
        base, call = base_and_span(span)
        data = loader.read_data(path, base, call)
        try:
            document = yamlio.load(data.text)
        except yamlio.YamlError as exc:
            issue = exc.issue
            raise _data_error(data, issue.start, issue.end, call,
                              problem=str(issue.args.get("problem", issue.kind))) from None
        return from_data(document.value)

    def load_json(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
        path = _path_argument("load_json", args, kwargs, span, ())
        base, call = base_and_span(span)
        data = loader.read_data(path, base, call)
        try:
            value = json.loads(data.text, parse_float=_json_number, parse_constant=_json_constant,
                               object_pairs_hook=_json_object)
        except json.JSONDecodeError as exc:
            offset = min(exc.pos, len(data.text))
            raise _data_error(data, offset, offset, call, problem=exc.msg) from None
        except ValueError as exc:
            raise _data_error(data, 0, 0, call, problem=str(exc)) from None
        return from_data(value)

    def load_csv(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
        path = _path_argument("load_csv", args, kwargs, span, ("types", "sep"))
        base, call = base_and_span(span)
        data = loader.read_data(path, base, call)
        types = kwargs.get("types")
        separator = kwargs.get("sep")
        return _parse_csv(interp, data, call, types, separator)

    def load_text(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> str:
        path = _path_argument("load_text", args, kwargs, span, ())
        base, call = base_and_span(span)
        data = loader.read_data(path, base, call)
        # The string limit of the core (P2404) applies as to any computed string.
        interp.meter.check_string(len(data.text), call)
        return data.text

    def sheet_loader(name: str, kind: str) -> Callable[..., Any]:
        def load(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
            path = _path_argument(name, args, kwargs, span, ("sheet", "range", "header", "types"))
            base, call = base_and_span(span)
            sheet = kwargs.get("sheet")
            if sheet is not None and not isinstance(sheet, str) and not (
                    isinstance(sheet, (int, Decimal)) and not isinstance(sheet, bool) and sheet == int(sheet)):
                raise core_error("P2322", call, function=name, problem="sheet must be a name or a number from 1")
            area = kwargs.get("range")
            if area is not None:
                try:
                    area = sheets.parse_range(area) if isinstance(area, str) else None
                except ValueError:
                    area = None
                if area is None:
                    raise core_error("P2322", call, function=name, problem="range must be like \"A1:D20\" or \"A3\"")
            header = kwargs.get("header", True)
            if not isinstance(header, bool):
                raise core_error("P2322", call, function=name, problem="header must be True or False")
            converters = _sheet_converters(name, kwargs.get("types"), call)
            data = loader.read_binary(path, base, call)

            def meter(count: int) -> None:
                interp.meter.step(call, count)

            try:
                rows = sheets.read(data, kind, sheet, area, header, converters, meter)
            except sheets.SheetError as exc:
                if exc.problem.startswith("TYPE:"):
                    _, column, value = exc.problem.split(":", 2)
                    kind_name = kwargs["types"][column] if column in kwargs["types"] else "?"
                    raise core_error("P2629", call, value=value, column=f"{column}, {exc.where}",
                                     type=kind_name) from None
                where = f"{path}" + (f", {exc.where}" if exc.where else "")
                raise core_error("P2630", call, problem=f"{where}: {exc.problem}") from None
            interp.meter.check_collection(len(rows), call)
            return rows

        return load

    return {name: Builtin(name, impl) for name, impl in
            (("load_yaml", load_yaml), ("load_json", load_json), ("load_csv", load_csv),
             ("load_ods", sheet_loader("load_ods", "ods")), ("load_xlsx", sheet_loader("load_xlsx", "xlsx")),
             ("load_text", load_text))}


def _sheet_converters(name: str, types: Any, call: Span) -> dict[str, Callable[[Any], Any]]:
    """Converters of typed columns of ``load_ods``/``load_xlsx``: cell values, not text."""
    converters: dict[str, Callable[[Any], Any]] = {}
    if types is None:
        return converters
    pairs = types.items() if hasattr(types, "items") else None
    if pairs is None:
        raise core_error("P2322", call, function=name, problem="types must be a dict")
    for column, kind in pairs:
        if kind not in CSV_TYPES:
            raise core_error("P2322", call, function=name,
                             problem=f"unknown column type '{kind}'; expected one of {', '.join(CSV_TYPES)}")
        converters[nfkc(str(column))] = _cell_converter(kind)
    return converters


def _cell_converter(kind: str) -> Callable[[Any], Any]:
    """A converter of a cell value (a number, a ``datetime``, a ``bool``, text or ``None``) to ``kind``."""
    text_converter = _CONVERTERS[kind]

    def convert(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return text_converter(value)
        is_number = isinstance(value, (int, Decimal)) and not isinstance(value, bool)
        if kind == "str":
            return sheets._plain(value)
        if kind == "decimal" and is_number:
            return value
        if kind == "money" and is_number:
            number = Decimal(value)
            if number != number.quantize(Decimal("0.01")):
                raise ValueError(value)
            return number.quantize(Decimal("0.01"))
        if kind == "float" and is_number:
            return float(value)
        if kind == "datetime":
            if isinstance(value, DateTime):
                return value
            if is_number:
                return sheets.serial_moment(Decimal(value), False)
        if kind == "bool":
            if isinstance(value, bool):
                return value
            if is_number and value in (0, 1):
                return value == 1
        raise ValueError(value)

    return convert


def _path_argument(name: str, args: list[Any], kwargs: dict[str, Any], span: Any,
                   keywords: tuple[str, ...]) -> str:
    if len(args) != 1 or not isinstance(args[0], str):
        raise core_error("P2322", span, function=name, problem="expected one path string")
    for key in kwargs:
        if key not in keywords:
            raise core_error("P2321", span, function=name, problem=f"got an unexpected keyword argument '{key}'")
    return args[0]


def _data_error(data: SourceFile, start: int, end: int, call: Span, **args: object) -> CoreError:
    """P2630 positioned in the data file, with the call site as a frame."""
    exc = CoreError(error("P2630", Span(data, start, max(start, end)), **args))
    exc.add_frame("call", call, "load")
    return exc


def _json_number(text: str) -> Any:
    """A JSON number with a point: ``decimal`` without an exponent, else ``float``."""
    if "e" in text.lower():
        return float(text)
    value = Decimal(text)
    if not digits_ok(value):
        raise ValueError(f"the number {text} has more than 64 significant digits")
    return value


def _json_constant(text: str) -> Any:
    raise ValueError(f"{text} is not allowed in data")


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        key = nfkc(key)  # 3.9: keys coinciding after NFKC are duplicates
        if key in result:
            raise ValueError(f"duplicate key '{key}'")
        result[key] = value
    return result


# ----------------------------------------------------------------------
# CSV
# ----------------------------------------------------------------------


def _detect_separator(first_line: str) -> str:
    return ";" if first_line.count(";") > first_line.count(",") else ","


def _line_span(data: SourceFile, line: int) -> Span:
    line = max(1, min(line, data.line_count))
    start = data.line_start(line)
    return Span(data, start, start + len(data.line_text(line)))


def _parse_csv(interp: Any, data: SourceFile, call: Span, types: Any, separator: Any) -> PList:
    text = data.text
    first_line = text.split("\n", 1)[0]
    if separator is None:
        separator = _detect_separator(first_line)
    if separator not in (",", ";"):
        raise core_error("P2322", call, function="load_csv", problem="sep must be ',' or ';'")
    converters: dict[str, Callable[[str], Any]] = {}
    if types is not None:
        pairs = types.items() if hasattr(types, "items") else None
        if pairs is None:
            raise core_error("P2322", call, function="load_csv", problem="types must be a dict")
        for column, kind in pairs:
            if kind not in CSV_TYPES:
                problem = f"unknown column type '{kind}'; expected one of {', '.join(CSV_TYPES)}"
                if kind in _OLD_TYPES:
                    problem += f" (use '{_OLD_TYPES[kind]}')"
                raise core_error("P2322", call, function="load_csv", problem=problem)
            converters[nfkc(str(column))] = _CONVERTERS[kind]
    reader = csv.reader(io.StringIO(text), delimiter=separator, quotechar='"', strict=True)
    try:
        header = next(reader)
    except StopIteration:
        raise _data_error(data, 0, 0, call, problem="the file is empty") from None
    except csv.Error as exc:
        raise _data_error(data, 0, 0, call, problem=str(exc)) from None
    names = [nfkc(name.strip()) for name in header]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise _wrap(_line_span(data, 1), call, "P2630", problem="field names must be non-empty and unique")
    for column in converters:
        if column not in names:
            raise core_error("P2322", call, function="load_csv", problem=f"types: no column '{column}'")
    rows = PList()
    while True:
        try:
            row = next(reader)
        except StopIteration:
            break
        except csv.Error as exc:
            raise _wrap(_line_span(data, reader.line_num), call, "P2630", problem=str(exc)) from None
        if not row or (len(row) == 1 and not row[0].strip()):
            continue  # blank line
        line = reader.line_num
        if len(row) != len(names):
            raise _wrap(_line_span(data, line), call, "P2630",
                        problem=f"{len(row)} values, expected {len(names)}")
        fields: dict[str, Any] = {}
        for name, value in zip(names, row):
            converter = converters.get(name)
            if converter is None:
                fields[name] = value
                continue
            try:
                fields[name] = converter(value)
            except ValueError:
                kind = next(k for k, v in _CONVERTERS.items() if v is converter)
                raise _wrap(_line_span(data, line), call, "P2629", value=value, column=name,
                            type=kind) from None
        rows.append(Record(fields))
        interp.meter.check_collection(len(rows), call)
        interp.meter.step(call, len(row))
    return freeze(rows)


def _wrap(span: Span, call: Span, code: str, **args: object) -> CoreError:
    exc = CoreError(error(code, span, **args))
    exc.add_frame("call", call, "load_csv")
    return exc


def _number_text(value: str) -> str | None:
    """Normalise a number of a typed column; ``None`` for an empty cell."""
    text = value.strip()
    if not text:
        return None
    for space in _GROUP_SPACES:
        text = text.replace(space, "")
    if not _NUMBER_RE.match(text):
        raise ValueError(value)
    return text.replace(",", ".")


def _to_decimal(value: str) -> Any:
    """``decimal``: an integer is kept with scale 0 (Python ``int``)."""
    text = _number_text(value)
    if text is None:
        return None
    number: Any = int(text) if _INT_RE.match(text) else Decimal(text)
    if not digits_ok(number):
        raise ValueError(value)
    return number


def _to_money(value: str) -> Decimal | None:
    number = _to_decimal(value)
    if number is None:
        return None
    number = Decimal(number)
    if number.as_tuple().exponent < -2:  # type: ignore[operator]
        raise ValueError(value)
    try:
        return number.quantize(Decimal("0.01"))
    except decimal.InvalidOperation:
        raise ValueError(value) from None


def _to_float(value: str) -> float | None:
    text = _number_text(value)
    return None if text is None else float(text)


_DMY_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})(?: (\d{2}):(\d{2})(?::(\d{2}))?)?")


def _to_datetime(value: str) -> DateTime | None:
    """``datetime`` of a CSV cell (10.5); a value with a zone is an error."""
    text = value.strip()
    if not text:
        return None
    try:
        match = _DMY_RE.fullmatch(text)
        if match:
            day, month, year, hour, minute, second = match.groups()
            return DateTime.of(int(year), int(month), int(day), int(hour or 0), int(minute or 0),
                               int(second or 0))
        return parse_iso_datetime(text)
    except DateTimeError:
        raise ValueError(value) from None


def _to_bool(value: str) -> bool | None:
    text = value.strip().lower()
    if not text:
        return None
    if text in ("true", "1"):
        return True
    if text in ("false", "0"):
        return False
    raise ValueError(value)


def _to_str(value: str) -> str:
    return value


_CONVERTERS: dict[str, Callable[[str], Any]] = {
    "str": _to_str, "decimal": _to_decimal, "money": _to_money,
    "float": _to_float, "datetime": _to_datetime, "bool": _to_bool,
}


class ImageValue(Record):
    """An image value made by ``img(path, …)`` or ``img(svg=text, …)`` in code (decisions 84, 131).

    Fields: ``path`` (the resolved file, a string) or ``svg`` (the checked
    SVG text), and the keyword options given (``height``, ``width``…); used
    in ``watermark=`` of page styles, in ``watermark(…)`` and as the image of
    ``|img(value)`` and ``|figure(value)`` (the options are defaults of the
    command's arguments).
    """


def checked_svg(text: Any, span: Any) -> Any:
    """Check the SVG string of ``svg=`` (decision 131) and return the image.

    Args:
        text: the value of ``svg=``.
        span: the place of the call or command, for the diagnostic.

    Returns:
        the :class:`~primula.pages.images.ImageInfo` of the string.

    Raises:
        CoreError: P6110 (not a string, not an SVG image), P6111 (DTD),
            P6112 (an external reference).
    """
    from primula.pages.images import SvgTextError, svg_from_text

    if not isinstance(text, str):
        raise core_error("P6110", span, reason=Key("svgtext.type"))
    try:
        return svg_from_text(text)
    except SvgTextError as exc:
        if exc.code == "P6110":
            raise core_error("P6110", span, reason=Key(f"svgtext.{exc.reason}")) from None
        if exc.code == "P6112":
            raise core_error("P6112", span, ref=exc.reason) from None
        raise core_error(exc.code, span) from None


def make_image_builtins(loader: Loader) -> dict[str, Builtin]:
    """The built-in ``img(path, …)`` / ``img(svg=text, …)`` (paths by the rules of 10.1)."""

    def img(interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> ImageValue:
        if "svg" in kwargs:
            if args:
                raise core_error("P2321", span, function="img", problem="takes either the image path or svg=, not both")
            checked_svg(kwargs["svg"], span)
            return ImageValue(dict(kwargs))
        if len(args) != 1 or not isinstance(args[0], str):
            raise core_error("P2321", span, function="img", problem="takes the image path as the only positional argument")
        real = resolve(span)
        path = loader.resolve(args[0], real.source, real)
        return ImageValue({"path": str(path), **kwargs})

    return {"img": Builtin("img", img)}
