"""Document evaluation (stage 13.3): markup + computing core -> evaluated tree.

Phases (decision 54):

1. **collect** definitions from the whole document and the fragments it
   includes (outside ``|if``/``|for``/``|def`` bodies, decision 49):
   header parameters, ``doc``, ``|let``, definitions of ``|code:`` blocks,
   ``|def`` macros, ``|import`` modules, fragment exports (10.4);
2. **run actions** of all ``|code:`` blocks in document order, fragments
   included (12.7, decision 40);
3. **evaluate markup**: expressions, ``|if``/``|for``, ``when=`` (9.2),
   macro and command calls (3.2, decision 48), ``|include`` insertion
   (transparent for regions, decision 31), then implicit regions and lists
   are built (:func:`primula.syntax.regions.organize`).

Scopes (10.4, decision 50):

* the root document has a :class:`GlobalScope` with the header
  parameters, ``doc``, its definitions and the exports of its fragments;
* a fragment has its own scope whose parent is the root document scope:
  it sees its own names and parameters, then the root document;
* a module has its own scope without a parent; it is bound in the
  importing file as ``module`` (:class:`ModuleValue`) or by name;
* bodies of ``|for`` and ``|def`` have local environments (decision 49).

Errors are reported with stack frames through ``|include`` and macro
calls; evaluation continues after an error, so independent problems are
all shown.
"""

from __future__ import annotations

import ast
import datetime
import keyword
from decimal import Decimal
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from primula.core.errors import CoreError, core_error, resolve
from primula.core.interp import EvalContext, Interpreter
from primula.core.limits import Limits, Meter
from primula.core.program import Action, Program
from primula.core.scope import Env, GlobalScope
from primula.core.values import (
    Builtin, BoundMethod, Content, DateTime, Function, Length, ModuleValue, PDict, PList, Record,
    freeze, from_data, to_repr, to_str, type_name,
)
from primula.diagnostics import Diagnostic, DiagnosticSink, error, warning
from primula.evaluate.data import ImageValue, checked_svg, make_data_builtins, make_image_builtins
from primula.evaluate.loader import LoadedFile, Loader, strip_extension
from primula.evaluate.model import EArgs, Macro, content_blocks, content_inline
from primula.header import Header
from primula.library.context import Library
from primula.library.prelude import make_library_builtins, std_module
from primula.source import SourceFile, Span
from primula.syntax import nodes as N
from primula.syntax import regions
from primula.syntax.blocks import BUILTIN_COMMANDS, RESERVED_NAMES
from primula.syntax.parser import parse
from primula.syntax.pyfrag import PyArgs
from primula.unicode import is_identifier, nfkc
from primula.core.values import parse_length
from primula.styles.apply import StyleApplier, merge_overrides
from primula.structure.tree import iter_tree
from primula.tables.columns import make_column_builtins
from primula.parallel import model as parallel_model
from primula.paths import within
from primula.parallel import parity as parallel_parity
from primula.parallel import rev as parallel_rev
from primula.parallel.build import EvaluatedSegment, build_tables
from primula.i18n import Key
from primula.tables.formulas import make_table_builtins
from primula.styles.functions import STRUCTURE_KEYS, load_yaml_groups, make_style_builtins
from primula.styles.system import StyleRegistry, StyleSystem
from primula.structure.settings import document_language

#: Arguments of ``|include`` that are not fragment parameters.
_INCLUDE_ARGS = ("path", "part", "key", "ns", "rename", "level_shift")
#: Arguments of ``|document`` (10.7).
_DOCUMENT_ARGS = ("path", "scope", "params", "page", "when", "level_shift")


@dataclass
class EvalOptions:
    """Options of an evaluation run.

    Attributes:
        build_date: value of ``build_date()``.
        review: ``--review`` mode (9.2): excluded blocks are kept and marked.
        limits: core limits.
        deadline: ``time.monotonic()`` at which the whole build stops
            (``--timeout``, 12.8), or ``None``.
        styles: styles modules of ``--style`` (11.7, decision 106).
    """

    build_date: datetime.date = field(default_factory=datetime.date.today)
    review: bool = False
    limits: Limits = field(default_factory=Limits)
    deadline: float | None = None
    styles: list[Path] = field(default_factory=list)
    #: The project (10.6, stage 13.11): :class:`~primula.evaluate.project.Project` or ``None``.
    project: Any = None
    #: The build target of a batch build (10.7): its parameters and keys.
    target: Any = None
    #: Value of ``batch_mode()``: ``True`` in ``primula build project.p.prml``.
    batch: bool = False
    #: Receives the targets of ``build()`` (batch planning), or ``None``.
    targets: list[Any] | None = None
    #: ``--param`` of the root document: name -> (value, text as written) (14.1, П2).
    params: dict[str, tuple[Any, str]] = field(default_factory=dict)
    #: The collections of the first pass that ``collected()`` returns in the second one
    #: (name -> values; decision 143), or ``None`` in the first pass.
    collected: dict[str, list[Any]] | None = None


@dataclass(eq=False)
class FileState:
    """One evaluated instance of a file (root document, fragment inclusion, module).

    Attributes:
        loaded: the parsed file.
        scope: its global scope.
        program: definitions and actions of its code.
        kind: ``document``, ``fragment`` or ``module``.
        frame: stack frame of its inclusion (``None`` for the root).
        exports: exported definitions ``(name, compute, span)``.
        overrides: names defined with ``override=True`` (root document).
    """

    loaded: LoadedFile
    scope: GlobalScope
    program: Program
    kind: str
    frame: tuple[str, Span, str] | None = None
    exports: list[tuple[str, Any, Span]] = field(default_factory=list)
    overrides: set[str] = field(default_factory=set)
    namespace: str | None = None
    rename: dict[str, str] = field(default_factory=dict)
    #: The document (root or a part of a compound document) a fragment belongs to.
    owner: "FileState | None" = None
    #: Scope name of a part ``|document(…, scope=…)`` (10.7), ``None`` elsewhere.
    part_scope: str | None = None


@dataclass
class EvaluationResult:
    """Result of evaluating a document.

    Attributes:
        document: the evaluated and organised tree.
        params: header parameters of the root document (for the report).
        conditions: ``when=`` conditions evaluated: ``(text, result, span)``.
        debug: ``debug()`` records.
        limits: limit usage.
        styles: the style system (stage 13.4).
        tables: computed column widths of tables for the report (6.3, stage 13.7).
        excluded_ids: literal ``id="…"`` of blocks excluded by ``when=`` or
            an ``|if`` branch: ID -> (condition text, condition span)
            (decision 75; stage 13.6 reports references to them).
        structure: the result of the structure phase (stage 13.6), set by
            :func:`primula.structure.build_structure`.
    """

    document: N.Document
    params: dict[str, Any]
    conditions: list[tuple[str, bool, Span]]
    debug: list[tuple[Span | None, str]]
    limits: dict[str, object]
    styles: StyleSystem | None = None
    excluded_ids: dict[str, tuple[str, Span]] = field(default_factory=dict)
    structure: Any = None
    #: Watermark text of the ``--review`` mode (9.2), or ``None``.
    review_watermark: str | None = None
    tables: list[dict[str, Any]] = field(default_factory=list)
    pages: Any = None
    #: Language of the project (10.6), the fallback after ``doc.language``.
    project_language: str | None = None
    #: Defaults of the ODT metadata: the ``doc_defaults`` key of the project (decisions 127, 129).
    document_defaults: dict[str, Any] = field(default_factory=dict)
    #: ``|include``/``|document`` places (``check --dump-structure``, stage 14.2).
    inclusions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class _Ctx:
    """Context of markup evaluation (phase 3)."""

    state: FileState
    env: Env
    local: bool = False          # inside a |for or |def body (decision 49)
    container: str | None = None  # enclosing table/row command (decision 37)


class _FrameSink(DiagnosticSink):
    """Adds the evaluator's include/macro frames to diagnostics."""

    def __init__(self, target: DiagnosticSink, frames: list[tuple[str, Span, str]]) -> None:
        super().__init__(strict=target.strict, error_limit=0)
        self.target = target
        self.frames = frames
        # Diagnostics already reported, by identity: the error of a failed
        # lazy definition is raised again at every later use of the name
        # (12.7) and must be reported once.
        self._emitted: dict[int, Diagnostic] = {}

    def emit(self, diagnostic: Diagnostic) -> Diagnostic:  # noqa: D102
        if id(diagnostic) in self._emitted:
            return self._emitted[id(diagnostic)]
        self._emitted[id(diagnostic)] = diagnostic
        for kind, span, name in reversed(self.frames):
            diagnostic.frame(kind, span, name)
        return self.target.emit(diagnostic)


@dataclass
class _BuiltinModule:
    """A built-in code module ``std/…``: only its global scope (names for ``|import``)."""

    scope: GlobalScope


class DocumentEvaluator:
    """Evaluates a root document with its fragments and modules.

    Args:
        loader: file loader of the project.
        sink: diagnostics receiver.
        options: evaluation options.
    """

    def __init__(self, loader: Loader, sink: DiagnosticSink, options: EvalOptions | None = None) -> None:
        self.loader = loader
        self.options = options or EvalOptions()
        self.frames: list[tuple[str, Span, str]] = []
        self.sink = _FrameSink(sink, self.frames)
        self.loader.sink = self.sink
        self.registry = StyleRegistry()
        # The standard library (stage 13.9): the document language is known
        # once the root header and the styles defaults are read.
        self.header_data: dict[str, Any] = {}
        self.library = Library(lambda: self.registry.settings,
                               lambda: self._language(), self.sink)
        builtins = {**make_library_builtins(self.library), **make_data_builtins(loader),
                    **make_style_builtins(self.registry),
                    **make_column_builtins(), **make_table_builtins(), **make_image_builtins(loader),
                    **parallel_model.make_parallel_builtins(),
                    "has": Builtin("has", self._has), "markup": Builtin("markup", self._markup),
                    "param": Builtin("param", self._fn_param), "collect": Builtin("collect", self._fn_collect), "collected": Builtin("collected", self._fn_collected),
                    "build": Builtin("build", self._build_target), "batch_mode": Builtin("batch_mode", self._batch_mode)}
        self.interp = Interpreter(EvalContext(meter=Meter(self.options.limits, deadline=self.options.deadline),
                                              build_date=self.options.build_date,
                                              sink=self.sink, extra_builtins=builtins))
        #: ``collect(name, value)`` of this pass, and whether ``collected()`` asked for the other pass (decision 143).
        self.collections: dict[str, list[Any]] = {}
        self.collected_used = False
        #: Names of the parameters of the root document (header, project; the values come from its scope) for ``param()`` (decision 144).
        self.root_params: set[str] = set()
        self.actions: list[tuple[Program, Action, FileState]] = []
        self.conditions: list[tuple[str, bool, Span]] = []
        self.excluded_ids: dict[str, tuple[str, Span]] = {}
        self.include_stack: list[Path] = []
        self.modules: dict[Path, FileState] = {}
        self.states_by_source: dict[int, FileState] = {}
        self.prepared: dict[int, FileState] = {}
        self.root: FileState | None = None
        #: The root document of the build (``self.root`` is the current part).
        self.document_root: FileState | None = None
        self.project_scope: GlobalScope | None = None
        #: ``|document`` commands of the root (phase 1) and the prepared parts.
        self.part_nodes: list[N.Command] = []
        self.parts: dict[int, FileState] = {}
        #: ``|document`` inside ``|if``/``|for`` or with ``when=`` (decision 118):
        #: prepared when the command is evaluated, once per evaluation.
        self.deferred_parts: set[int] = set()
        #: Scope names of the parts already prepared (unique, 10.7).
        self.part_scopes: set[str] = set()
        #: Depth of environments around the block being collected (``|document`` check).
        self._env_depth = 0
        #: Places of ``|include`` and ``|document`` in document order, once each
        #: (``check --dump-structure``, stage 14.2): kind, span, path, ns/part/scope.
        self.inclusions: list[dict[str, Any]] = []
        self._inclusion_keys: set[tuple[int, int, Path]] = set()
        #: Open ``|parallel`` environments (7.7) and the segment IDs of the document.
        self.parallel_stack: list[parallel_model.ParallelSpec] = []
        self.segment_ids: dict[str, Span] = {}
        #: Languages of the track blocks being evaluated (7.7): the library
        #: functions follow the innermost one instead of the document language.
        self.track_languages: list[str] = []

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------

    def evaluate(self, root: LoadedFile) -> EvaluationResult:
        """Evaluate a root document (or a fragment built on its own)."""
        state, params = self._prepare(root)
        scope = state.scope
        return self._finish(root, state, scope, params)

    def prepare(self, root: LoadedFile) -> GlobalScope:
        """The names of a document without its text (the console, decision 128).

        The project, the styles, the header parameters and ``doc``, the
        definitions of the code (phase 1) and its actions (phase 2); the
        markup is not evaluated.

        Returns:
            The global scope of the document.
        """
        state, _params = self._prepare(root)
        return state.scope

    def module_scope(self, path: Path) -> GlobalScope:
        """The names of a module, as ``|import`` loads it (the console, decision 128)."""
        span = Span(SourceFile.from_text(str(path), ""), 0, 0)
        loaded = self.loader.load(path, span)
        if loaded.header.kind != "module":
            raise core_error("P2616", span, path=str(path), kind=loaded.header.kind, expected="module")
        self.project_scope = self._load_project()
        scope = self.interp.new_globals(parent=self.project_scope)
        module = FileState(loaded, scope, Program(self.interp, scope), "module")
        self.modules[path] = module
        self.states_by_source[id(loaded.source)] = module
        saved_layer, self.registry.current = self.registry.current, None
        try:
            self._check_module(loaded)
            self._collect(loaded.document.children, module, in_if=False, local=False)
            for program, action, _owner in self.actions:
                program.run_action(action, self.sink)
            self.actions.clear()
        finally:
            self.registry.current = saved_layer
        return scope

    def _prepare(self, root: LoadedFile) -> tuple[FileState, Any]:
        """Phases 1 and 2 of :meth:`evaluate`: definitions and actions of the code."""
        self.header_data = root.header.data if isinstance(root.header.data, dict) else {}
        self.project_scope = self._load_project()
        self.styles_scope = self._load_styles(root)
        scope = self.interp.new_globals(parent=self.styles_scope)
        self.registry.begin_layer("document")
        state = FileState(root, scope, Program(self.interp, scope), "document")
        self.root = self.document_root = state
        self.states_by_source[id(root.source)] = state
        self.include_stack.append(root.path)
        target = self.options.target
        values = target.params if target is not None else self._param_options(state)
        params = self._define_header(state, None, values=values)
        project = self.options.project
        self.root_params = set(params) | (set(project.params) if project is not None else set())
        self._define_doc(state)

        # Phase 1: definitions.
        self._collect(root.document.children, state, in_if=False, local=False)
        self._merge_exports()
        # Parts of a compound document (10.7): each with its own names.
        for node in self.part_nodes:
            try:
                self.parts[id(node)] = self._prepare_part(node, None)
            except CoreError as exc:
                self.report(exc)
        # Phase 2: actions in document order.
        for program, action, owner in self.actions:
            self.interp.meter.begin()  # each action is one evaluation (12.8)
            self._with_frame(owner, lambda: program.run_action(action, self.sink))
        return state, params

    def _finish(self, root: LoadedFile, state: FileState, scope: GlobalScope, params: Any) -> EvaluationResult:
        """Phases 3 and later of :meth:`evaluate`: markup, styles, techdoc, tables."""
        # Phase 3: markup.
        flat = self._expand_blocks(root.document.children, _Ctx(state, Env(scope)))
        self.include_stack.pop()
        document = replace(root.document, children=regions.organize(flat, self.sink))
        # Styles (stage 13.4): merge the layers, then annotate the tree.
        system = self.registry.finalize(self.sink)
        # Technical documentation (stage 13.10): |! blocks, abbreviations and
        # --review marks become ordinary nodes before the styles are applied.
        review = self._techdoc(document, system)
        StyleApplier(system, self.sink, self._scale).apply(document)
        self._check_list_formats(system, document)
        if review is not None:
            review.after_styles()
        # Tables (stage 13.7): values, formulas, column widths.
        from primula.tables.process import TableProcessor

        tables = TableProcessor(self.interp, system, self.sink, root.header.data, self.library,
                                self._project_language()).process(document)
        self._lint_names(system)
        result = EvaluationResult(document, params, self.conditions, self.interp.ctx.debug,
                                  self.interp.meter.usage(), system, self.excluded_ids, tables=tables)
        result.review_watermark = review.watermark if review is not None else None
        result.project_language = self._project_language()
        result.document_defaults = self._document_defaults()
        result.inclusions = self.inclusions
        return result

    def _record_inclusion(self, kind: str, node: N.Command, path: Path, **details: Any) -> None:
        """Remember an ``|include``/``|document`` for the structure dump (once per place and file)."""
        key = (id(node.span.source), node.span.start, path)
        if key in self._inclusion_keys:
            return
        self._inclusion_keys.add(key)
        self.inclusions.append({"kind": kind, "span": node.span, "path": path,
                                **{k: v for k, v in details.items() if v is not None}})

    # ------------------------------------------------------------------
    # The project (10.6, 10.7; decision 117)
    # ------------------------------------------------------------------

    def _project_language(self) -> str | None:
        """The fallback after ``doc.language`` of the header: ``doc_defaults.language``
        of the project (its metadata defaults, decisions 127, 129), then the project ``language``."""
        project = self.options.project
        if project is None:
            return None
        language = project.doc_defaults.get("language")
        return language if isinstance(language, str) and language else project.language

    def _document_defaults(self) -> dict[str, Any]:
        """Defaults of the document metadata: the ``doc_defaults`` key of the project (decisions 127, 129)."""
        project = self.options.project
        return dict(project.doc_defaults) if project is not None else {}

    def _language(self) -> str:
        """Language of the current document or part (10.7: a part uses its own ``language``);
        inside a track block with ``lang`` — the language of the track (7.7)."""
        if self.track_languages:
            return self.track_languages[-1]
        return document_language(self.header_data, self.registry.defaults, self._project_language())

    def run_project(self) -> None:
        """Run the code section of the project alone (batch planning, ``check project.p.prml``)."""
        self.project_scope = self._load_project()

    def _load_project(self) -> GlobalScope:
        """The "project" name level: parameters, ``project``, the code section (10.4, 10.6).

        The descriptive parameters are defined as values (the code section
        cannot redefine them: P2203); ``project`` gives ``project.city``
        regardless of a document parameter of the same name.  Definitions of
        the code section are lazy, its top-level actions run now (decision
        117); styles cannot be defined there (no layer).
        """
        from primula.core.check import check_document

        scope = self.interp.new_globals()
        project = self.options.project
        if project is None:
            return scope
        for name, (value, span) in project.params.items():
            scope.define_value(name, value, span)
        module = ModuleValue("project", scope)
        scope.define_value("project", module, None)
        # The code sections of the base projects (extends, decision 123) run first,
        # each in its own level: a later project may redefine a name of its base.
        for index, current in enumerate([*project.bases, project]):
            if index:
                scope = self.interp.new_globals(parent=scope)
                module.scope = scope  # project.* sees the latest level
            if not self._project_code(current, scope):
                break
        return scope

    def _project_code(self, project: Any, scope: GlobalScope) -> bool:
        """Run the code section of one project file in ``scope``; ``False`` after syntax errors."""
        from primula.core.check import check_document

        errors = self.sink.error_count
        document = parse(project.header, self.sink, organize=False)
        for problem in check_document(document):
            self.sink.emit(problem)
        if self.sink.error_count > errors:
            return False
        loaded = LoadedFile(project.path, project.source, project.header, document)
        state = FileState(loaded, scope, Program(self.interp, scope), "project")
        self.states_by_source[id(project.source)] = state
        saved, self.registry.current = self.registry.current, None
        try:
            for block in document.children:
                if isinstance(block, N.CodeBlock) and block.code is not None:
                    state.program.add_code(block.code, self.sink)
            self._take_code_exports(state)
            for action in state.program.actions:
                self.interp.meter.begin()
                state.program.run_action(action, self.sink)
        finally:
            self.registry.current = saved
        return True

    def _project_call(self, name: str, span: Any) -> None:
        """``build()`` and ``batch_mode()`` exist only in the code section of the project (10.7): P7111."""
        project = self.options.project
        if project is None or resolve(span).source is not project.source:
            raise core_error("P7111", span, function=name)

    def _batch_mode(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> bool:
        """``batch_mode()``: ``True`` in ``primula build project.p.prml`` (decision 117)."""
        self._project_call("batch_mode", span)
        if args or kwargs:
            raise core_error("P2322", span, function="batch_mode", problem="takes no arguments")
        return self.options.batch

    def _build_target(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> None:
        """``build(source, params=…, keys=…, output=…, pdf=…)`` registers a target (10.7)."""
        from primula.evaluate.project import target_from_call

        self._project_call("build", span)
        target = target_from_call(args, kwargs, resolve(span))
        if self.options.targets is not None:
            self.options.targets.append(target)

    def _key_path(self, key: Any, span: Span, *, include: bool) -> tuple[Path, str | None]:
        """Resolve a key of the key map (9.3): a path from the project root and the part.

        Raises:
            CoreError: P7112 without a project, P2619 for an unknown key,
                P7113 for ``#part`` outside ``|include``, P2613 for a path
                outside the project.
        """
        project = self.options.project
        if project is None:
            raise core_error("P7112", span)
        keys = {name: text for name, (text, _span) in project.keys.items()}
        if self.options.target is not None:
            keys.update(self.options.target.keys)
        name = nfkc(key) if isinstance(key, str) else key
        text = keys.get(name) if isinstance(name, str) else None
        if text is None:
            raise core_error("P2619", span, key=to_str(key))
        path_text, _hash, part = text.partition("#")
        if part and not include:
            raise core_error("P7113", span, key=name, value=text)
        return self.loader.resolve_root(path_text, span), part or None

    def _techdoc(self, document: N.Document, system: StyleSystem) -> Any:
        """``|!`` blocks, ``|abbr``, ``--review`` marks (9.1, 9.2, 9.4; decision 116).

        Returns:
            The :class:`~primula.techdoc.review.ReviewMarks` of the ``--review``
            mode (backgrounds are added after the styles), or ``None``.
        """
        from primula.techdoc.abbreviations import AbbreviationTransform
        from primula.techdoc.admonitions import AdmonitionTransform
        from primula.techdoc.review import ReviewMarks
        from primula.techdoc.texts import language

        lang = language(self._language())
        settings = self.registry.settings
        definition = self.styles_scope.definitions.get("admonition") if self.styles_scope is not None else None
        if definition is not None:
            self.sink.emit(warning("P9105", definition.span))

        def resolve(path: str, span: Any) -> Any:
            try:
                return self.loader.resolve(path, span.source, span)
            except CoreError as exc:
                self.report(exc)
                return None

        AdmonitionTransform(settings, system.effective, lang, self.sink, resolve,
                            self.registry.setting_spans.get("admonition_symbols")).apply(document)
        AbbreviationTransform(settings, lang, self.sink).apply(document)
        if not self.options.review:
            return None
        review = ReviewMarks(settings, system.effective, lang)
        review.before_styles(document)
        return review

    def _check_list_formats(self, system: StyleSystem, document: N.Document) -> None:
        """Cyrillic list numbering (``а``, ``А``) needs a uk or ru document (11.3): P3121.

        Only the list styles the document uses are checked (decision 133): a
        styles set of the kit may define a Cyrillic list and still serve a
        document in English; an unused style is written with Latin letters.
        """
        from primula.structure.tree import iter_tree

        code = (self._language() or "").split("-")[0].lower()
        if code in ("uk", "ru"):
            return
        used: dict[str, Any] = {}
        for node in iter_tree(document.children):
            name = getattr(node, "list_style", None) if isinstance(node, N.ListBlock) else None
            if isinstance(name, str):
                used.setdefault(name, node)
        for name, node in used.items():
            levels = system.effective(name).get("levels") or {}
            for props in levels.values():
                fmt = props.get("format") if isinstance(props, dict) else None
                if fmt in ("а", "А"):
                    definition = system.styles.get(name)
                    span = definition.span if definition is not None and definition.span is not None else node.span
                    self.sink.emit(error("P3121", span, name=name, format=fmt).hint("help.list_cyrillic"))
                    break

    def _lint_names(self, system: StyleSystem) -> None:
        """Warnings about look-alike author names (3.9): P2502, P2503."""
        from primula.evaluate.lint import lint_names

        names: list[tuple[str, Span | None]] = []
        for state in [self.root, *self.states_by_source.values()]:
            if state is None or self.loader.display_name(state.loaded.path).startswith("std/"):
                continue
            names += [(name, definition.span) for name, definition in state.scope.definitions.items()]
        names += [(name, definition.span) for name, definition in system.styles.items()
                  if definition.layer != -1  # materialised names are not written by the author
                  and definition.span is not None and definition.span.source.path is not None
                  and not self.loader.display_name(definition.span.source.path).startswith("std/")]
        lint_names(names, self.sink)

    def _with_frame(self, state: FileState, action: Any) -> Any:
        if state.frame is None:
            return action()
        self.frames.append(state.frame)
        try:
            return action()
        finally:
            self.frames.pop()

    def report(self, exc: CoreError) -> None:
        """Report a core error with the current frames."""
        self.sink.emit(exc.diagnostic)

    # ------------------------------------------------------------------
    # Styles modules (11.1, 11.7, decisions 55, 58)
    # ------------------------------------------------------------------

    def _load_styles(self, root: LoadedFile) -> GlobalScope:
        """Load the styles modules as layers; return the "styles" name level.

        Layers (11.7, decision 106): the project list (paths relative to the
        project file), the ``--style`` files in the given order, the document header key
        ``styles``; when none of them names a module, the built-in module
        ``std/styles/default`` is used (decision 55).  Public names of the
        modules form a scope between the document and the project
        (decision 58); a later module replaces a name of an earlier one.
        """
        header = root.header
        names = header.data.get("styles")
        if isinstance(names, str):
            names = [names]
        span = header.value_span(("styles",)) or Span(root.source, 0, 0)
        # (path text, resolved path or None, origin) of every layer, in order;
        # the origin is shown by ``check --dump-styles`` (stage 14.2).
        layers: list[tuple[str, Path | None, str]] = []
        project = self.options.project
        if project is not None:
            for text in project.styles:
                try:
                    found = self.loader.find(self.loader.resolve(text, project.source, project.span("styles")),
                                             "styles")
                except CoreError as exc:
                    self.report(exc)
                    continue
                layers.append((text, found, "project"))
        layers += [(str(p), self.loader.resolve_option(str(p)), "option") for p in self.options.styles]
        layers += [(text, None, "header") for text in names or []]
        if not layers:
            layers = [("std/styles/default", None, "default")]
        # The "styles" level grows module by module: a module sees the public
        # names of the modules before it (a local layer uses `spacing` of the
        # base one); a later name replaces an earlier one (11.7).  Above it
        # is the project level (10.4).
        styles_scope = self.interp.new_globals(parent=self.project_scope)
        done: set[Path] = set()
        for text, given, origin in layers:
            if isinstance(text, str):
                self._load_styles_layer(text, given, origin, root.source, span, styles_scope, done, [])
        return styles_scope

    def _load_styles_layer(self, text: str, given: Path | None, origin: str, base: SourceFile, span: Span,
                           styles_scope: GlobalScope, done: set[Path], chain: list[Path]) -> None:
        """Load one styles module as a layer, its base (``extends``) first (decision 133).

        Args:
            text: the path as written (in a list of styles or in ``extends``).
            given: the path already resolved (project list, ``--style``), or ``None``.
            origin: where the layer comes from: ``project``, ``option``,
                ``header``, ``default`` or ``extends`` (shown by ``--dump-styles``).
            base: the file whose directory a relative ``text`` is resolved from.
            span: position for errors (the list of styles or the ``extends`` value).
            styles_scope: the "styles" name level the public names go to.
            done: modules already loaded; each module is one layer, at its
                first place (a base named again later is not loaded again).
            chain: the modules whose base is being loaded (cycle check).
        """
        try:
            path = given or self.loader.find(self._styles_path(text, base, span), "styles")
            key = path.resolve()
            if key in chain:
                names = " -> ".join(self.loader.display_name(p) for p in [*chain, key])
                raise core_error("P2615", span, chain=names)
            if key in done:
                return
            loaded = self.loader.load(path, span)
            if loaded.header.kind != "styles":
                raise core_error("P2616", span, path=text, kind=loaded.header.kind, expected="styles")
        except CoreError as exc:
            self.report(exc)
            return
        parent = loaded.header.data.get("extends")
        if isinstance(parent, str):
            parent_span = loaded.header.value_span(("extends",)) or Span(loaded.source, 0, 0)
            self._load_styles_layer(parent, None, "extends", loaded.source, parent_span, styles_scope, done,
                                    [*chain, key])
        if key in done:   # reached again through its own base: reported as a cycle above
            return
        done.add(key)
        scope = self.interp.new_globals(parent=styles_scope)
        state = FileState(loaded, scope, Program(self.interp, scope), "styles", frame=("import", span, ""))
        self.states_by_source[id(loaded.source)] = state
        self.registry.begin_layer(self.loader.display_name(loaded.path), origin)
        self.registry.modules.append(self.loader.display_name(loaded.path))
        self.frames.append(state.frame)  # type: ignore[arg-type]
        try:
            load_yaml_groups(self.registry, loaded.header,
                             lambda exc: self.report(exc) if isinstance(exc, CoreError) else None)
            for block in loaded.document.children:
                if isinstance(block, N.CodeBlock) and block.code is not None:
                    state.program.add_code(block.code, self.sink)
            self._take_code_exports(state)
            state.program.run_actions(self.sink)
        finally:
            self.frames.pop()
        for name in list(scope.definitions):
            if not name.startswith("_"):
                styles_scope.definitions.pop(name, None)
                styles_scope.define(name, lambda n=name, s=scope: s.lookup(n, None), None)

    def _styles_path(self, text: str, base: SourceFile, span: Span) -> Path:
        """Path of a styles module named in a list of styles or in ``extends``.

        A module outside the project root (a ``--style`` file, decision 106)
        names its base relative to its own directory; the root limit does not
        apply to it, as it does not apply to the module itself.
        """
        if base.path is not None and not text.startswith("std/") and within(base.path, self.loader.root) is None:
            if not text or "://" in text or Path(text).is_absolute():
                raise core_error("P2613", span, path=text)
            return (base.path.parent / text).resolve()
        return self.loader.resolve(text, base, span)

    def _scale(self, kind: str, value: Any, span: Span | None) -> Any:
        """Length of a spacing step or an indent (11.4): ``spacing``, ``indent_step``."""
        from primula.core.values import Length

        if isinstance(value, Length):
            return value
        if isinstance(value, str) and parse_length(value) is not None:
            return parse_length(value)
        if kind == "indent" and isinstance(value, int) and not isinstance(value, bool):
            step = self._styles_name("indent_step", span)
            if not isinstance(step, Length):
                raise core_error("P3112", span, step=str(value), scale="indent_step")
            return Length(step.value * value, step.unit)
        if kind == "spacing" and isinstance(value, str):
            spacing = self._styles_name("spacing", span)
            mapping = spacing.fields if isinstance(spacing, Record) else spacing
            if isinstance(mapping, (dict, PDict)) and isinstance(mapping.get(value), Length):
                return mapping[value]
        raise core_error("P3112", span, step=str(value), scale="spacing" if kind == "spacing" else "indent_step")

    def _styles_name(self, name: str, span: Span | None) -> Any:
        if not self.styles_scope.has(name):
            return None
        return self.styles_scope.lookup(name, span)

    # ------------------------------------------------------------------
    # Header: params and doc
    # ------------------------------------------------------------------

    def _param_options(self, state: FileState) -> dict[str, Any] | None:
        """Check ``--param`` against the parameters of the root document and the project (П2).

        A name declared neither in the document nor in the project is P7124;
        a value of another type than the declaration is P7106.  A string
        parameter takes the text as written (``--param num=42`` gives «42»),
        so a number-like text needs no quotes.  Both errors are reported
        without a position: the value comes from the command line.

        Returns:
            Name -> value for :meth:`_define_header`, or ``None`` without ``--param``.
        """
        from primula.evaluate.project import same_type

        if not self.options.params:
            return None
        declared = {nfkc(name): from_data(value) for name, value in (state.loaded.header.data.get("params") or {}).items()
                    if isinstance(name, str)}
        project = self.options.project
        if project is not None:
            for name, (value, _span) in project.params.items():
                declared.setdefault(name, value)
        path = self.loader.display_name(state.loaded.path)
        values: dict[str, Any] = {}
        for name, (value, text) in self.options.params.items():
            if name not in declared:
                self.sink.emit(error("P7124", None, at_file=path, name=name, path=path))
                continue
            expected = declared[name]
            if isinstance(expected, str):
                value = text
            if not same_type(value, expected):
                self.sink.emit(error("P7106", None, at_file=path, name=name, type=type_name(value),
                                     expected=type_name(expected)))
                continue
            values[name] = value
        return values

    def _define_header(self, state: FileState, given: dict[str, Any] | None, *,
                       values: dict[str, Any] | None = None, values_span: Span | None = None) -> dict[str, Any]:
        """Define header parameters.

        Args:
            state: the file.
            given: fragment parameters of ``|include``: name -> (expression,
                fragment, environment), evaluated lazily.
            values: parameter values of a document: a build target (10.7) or
                ``params=`` of a part; a name declared only in the project is
                defined in the document too (decision 117).
            values_span: position of ``values`` for errors.

        A document parameter with the name of a project parameter overrides
        it for this document; the types must agree (P7110).  Values are
        checked against the declaration (P7106); unknown names are P2617.

        Returns:
            Parameter name -> value for the report.
        """
        from primula.evaluate.project import same_type

        header = state.loaded.header
        declared = header.data.get("params") or {}
        given = given or {}
        values = values or {}
        project = self.options.project
        project_params = project.params if project is not None and state.kind == "document" else {}
        report: dict[str, Any] = {}
        for name, value in declared.items():
            span = header.value_span(("params", name), key=True) or Span(state.loaded.source, 0, 0)
            if not isinstance(name, str) or not is_identifier(name) or keyword.iskeyword(name):
                self.report(core_error("P2634", span, name=str(name)))
                continue
            name = nfkc(name)
            declared_value = from_data(value)
            if name in project_params and not same_type(declared_value, project_params[name][0]):
                self.report(core_error("P7110", span, name=name, type=type_name(declared_value),
                                       expected=type_name(project_params[name][0])))
            try:
                if name in given:
                    expr, frag, env = given[name]
                    state.scope.define(name, lambda e=expr, f=frag, v=env: self.interp.eval(e, v, f), span)
                elif name in values:
                    if not same_type(values[name], declared_value):
                        self.report(core_error("P7106", values_span or span, name=name, type=type_name(values[name]),
                                               expected=type_name(declared_value)))
                    state.scope.define_value(name, values[name], span)
                    report[name] = values[name]
                    continue
                else:
                    state.scope.define_value(name, declared_value, span)
            except CoreError as exc:
                self.report(exc)
            report[name] = value
        for name, (expr, frag, _env) in given.items():
            if name not in declared:
                self.report(core_error("P2617", frag.span_of(expr), name=name,
                                       path=self.loader.display_name(state.loaded.path)))
        for name, value in values.items():
            if name in report:
                continue
            if name in project_params:
                if not same_type(value, project_params[name][0]):
                    self.report(core_error("P7106", values_span or header.span, name=name, type=type_name(value),
                                           expected=type_name(project_params[name][0])))
                state.scope.define_value(name, value, values_span)
                report[name] = value
            else:
                self.report(core_error("P2617", values_span or header.span, name=name,
                                       path=self.loader.display_name(state.loaded.path)))
        return report

    def _define_doc(self, state: FileState) -> None:
        """``doc`` — metadata of the ``document`` header key (2.3) over the project defaults (10.6)."""
        metadata = state.loaded.header.data.get("doc") or {}
        if isinstance(metadata, dict):
            state.scope.define_value("doc", from_data({**self._document_defaults(), **metadata}), None)

    # ------------------------------------------------------------------
    # Phase 1: collecting definitions
    # ------------------------------------------------------------------

    def _collect(self, blocks: list[Any], state: FileState, *, in_if: bool, local: bool) -> None:
        for block in blocks:
            try:
                self._collect_block(block, state, in_if=in_if, local=local)
            except CoreError as exc:
                self.report(exc)

    def _definition_place_error(self, block: Any, what: str) -> None:
        self.report(CoreError(error("P2608", block.span, what=what).hint("help.conditional_definition")))

    def _collect_block(self, block: Any, state: FileState, *, in_if: bool, local: bool) -> None:
        if isinstance(block, N.CodeBlock):
            if local:
                return
            if in_if:
                self._definition_place_error(block, "|code:")
                return
            if block.code is not None:
                before = len(state.program.actions)
                state.program.add_code(block.code, self.sink)
                for action in state.program.actions[before:]:
                    self.actions.append((state.program, action, state))
                self._take_code_exports(state)
            return
        if isinstance(block, N.DefBlock):
            if local:
                return
            if in_if:
                self._definition_place_error(block, "|def")
                return
            state.scope.define(block.name, lambda b=block: self._make_macro(b, state.scope, state), block.span)
            return
        if isinstance(block, (N.Command, N.InlineCommand)) and block.name in ("let", "export", "import", "include",
                                                                             "document"):
            self._collect_command(block, state, in_if=in_if, local=local)
            return
        if isinstance(block, N.IfBlock):
            for branch in block.branches:
                self._collect(branch.children, state, in_if=in_if or not local, local=local)
            return
        if isinstance(block, N.ForBlock):
            self._collect(block.children, state, in_if=in_if, local=True)
            return
        if isinstance(block, (N.Command, N.Clause, N.Admonition, N.StyleBlock)) and block.form == "env":
            self._env_depth += 1
            try:
                self._collect(block.children, state, in_if=in_if, local=local)
            finally:
                self._env_depth -= 1
        for inline_list in _inline_lists(block):
            self._collect_inlines(inline_list, state, in_if=in_if, local=local)

    def _collect_inlines(self, inlines: list[Any], state: FileState, *, in_if: bool, local: bool) -> None:
        for node in inlines:
            if isinstance(node, N.InlineCommand) and node.name in ("let", "export", "import"):
                try:
                    self._collect_command(node, state, in_if=in_if, local=local)
                except CoreError as exc:
                    self.report(exc)
            elif isinstance(node, N.InlineIf):
                for branch in node.branches:
                    self._collect_inlines(branch.body, state, in_if=in_if or not local, local=local)
            elif isinstance(node, N.InlineFor):
                self._collect_inlines(node.body, state, in_if=in_if, local=True)
            elif getattr(node, "body", None):
                self._collect_inlines(node.body, state, in_if=in_if, local=local)

    def _collect_command(self, node: Any, state: FileState, *, in_if: bool, local: bool) -> None:
        name = node.name
        if name == "document":
            # Parts of a compound document: a line of the root document's text,
            # also inside |if/|for, not in an environment, a part or a fragment
            # (10.7, decision 118).
            if state is not self.document_root or self._env_depth or not isinstance(node, N.Command) \
                    or node.form != "bare":
                raise core_error("P7116", node.span)
            if local or in_if or (node.args is not None and node.args.keyword("when") is not None):
                # Its path, scope and parameters may depend on the loop or the
                # condition: the part is prepared when the command is evaluated.
                self.deferred_parts.add(id(node))
            else:
                self.part_nodes.append(node)
            return
        if name == "include":
            if not local and not in_if and isinstance(node, N.Command):
                prepared = self._prepare_include(node, _Ctx(state, Env(state.scope)), deferred=False)
                if prepared is not None:
                    self.prepared[id(node)] = prepared
            return
        if local:
            return
        if in_if:
            self._definition_place_error(node, "|" + name)
            return
        if name == "let":
            self._collect_let(node, state)
        elif name == "export":
            self._collect_export(node, state)
        elif name == "import":
            self._import(node, state)

    def _service_flag(self, args: PyArgs, name: str) -> bool:
        value = args.keyword(name)
        if value is None:
            return False
        if isinstance(value, ast.Constant) and isinstance(value.value, bool):
            return value.value
        raise core_error("P2609", args.fragment.span_of(value), command="let",
                         problem=f"'{name}' must be True or False")

    def _collect_let(self, node: Any, state: FileState) -> None:
        """Global ``|let(name=value, export=…, override=…)`` (10.4)."""
        args: PyArgs | None = node.args
        if args is None:
            return
        if args.call.args:
            raise core_error("P2609", args.span, command="let", problem="only name=value arguments")
        export = self._service_flag(args, "export")
        override = self._service_flag(args, "override")
        if export and state.kind != "fragment":
            raise core_error("P2610", args.span)
        frag = args.fragment
        for keyword_node in args.call.keywords:
            if keyword_node.arg in ("export", "override"):
                continue
            if keyword_node.arg is None:
                raise core_error("P2609", args.span, command="let", problem="**mapping is not allowed")
            name = keyword_node.arg
            span = frag.span_of(keyword_node)
            state.scope.define(name, lambda v=keyword_node.value: self.interp.eval(v, Env(state.scope), frag), span)
            if override:
                state.overrides.add(name)
            if export:
                state.exports.append((name, lambda n=name, s=state.scope: s.lookup(n, None), span))

    def _take_code_exports(self, state: FileState) -> None:
        """Exports of ``@export def`` registered by the program of ``state`` (decision 135).

        A fragment exports them like ``|export``; in a module every public
        name is visible without export (warning P2638); elsewhere an export
        is an error (P2610).  Each export is taken once.
        """
        exports, state.program.exports = state.program.exports, []
        for exported, name, span in exports:
            if state.kind == "fragment":
                state.exports.append((exported, lambda n=name, s=state.scope: s.lookup(n, None), span))
            elif state.kind == "module":
                self.sink.emit(warning("P2638", span, name=name))
            else:
                self.report(CoreError(error("P2610", span)))

    def _collect_export(self, node: Any, state: FileState) -> None:
        """``|export(name=value)`` and ``|export("name", …)`` in a fragment (10.4, decision 135).

        A string argument exports a name the fragment already defines
        (``|def`` macro, function, ``|let``, parameter) under the same name;
        a missing name is P2637 when the exports are merged.
        """
        args: PyArgs | None = node.args
        if args is None:
            return
        if state.kind != "fragment":
            raise core_error("P2610", args.span)
        frag = args.fragment
        for arg_node in args.call.args:
            if not (isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, str)
                    and arg_node.value.isidentifier()):
                raise core_error("P2609", frag.span_of(arg_node), command="export",
                                 problem="a name to export is a string with an identifier")
            name = arg_node.value
            span = frag.span_of(arg_node)
            state.exports.append((name, lambda n=name, s=state.scope, sp=span: _exported(s, n, sp), span))
        for keyword_node in args.call.keywords:
            if keyword_node.arg is None:
                raise core_error("P2609", args.span, command="export", problem="**mapping is not allowed")
            name = keyword_node.arg
            span = frag.span_of(keyword_node)
            state.scope.define(name, lambda v=keyword_node.value: self.interp.eval(v, Env(state.scope), frag), span)
            state.exports.append((name, lambda n=name, s=state.scope: s.lookup(n, None), span))

    def _merge_exports(self) -> None:
        """Register fragment exports in the root scope (10.4, ``ns=``, ``rename=``)."""
        assert self.root is not None
        root = self.root
        project = self.options.project
        mode = project.on_conflict if project is not None else "error"
        seen: dict[str, Span] = {}
        namespaces: dict[str, dict[str, Any]] = {}
        for state in self._fragment_states():
            for name, compute, span in state.exports:
                target = state.rename.get(name, name)
                if state.namespace:
                    namespaces.setdefault(state.namespace, {})[target] = compute
                    continue
                if target in seen:
                    if mode == "error":
                        self.report(CoreError(error("P2620", span, name=target)
                                              .note("note.first_definition", seen[target])))
                        continue
                    # on_conflict "first" keeps the first export, "last" the last one (10.4).
                    self.sink.emit(warning("P7115", span, name=target, mode=mode)
                                   .note("note.first_definition", seen[target]))
                    if mode == "last":
                        root.scope.definitions.pop(target, None)
                        root.scope.define(target, compute, span)
                        seen[target] = span
                    continue
                if target in root.scope.definitions:
                    if target in root.overrides:
                        continue
                    diagnostic = error("P2621", span, name=target)
                    first = root.scope.definitions[target].span
                    if first is not None:
                        diagnostic.note("note.first_definition", first)
                    self.report(CoreError(diagnostic))
                    continue
                seen[target] = span
                root.scope.define(target, compute, span)
        for namespace, computes in namespaces.items():
            try:
                root.scope.define(namespace, lambda c=computes: Record({k: f() for k, f in c.items()}), None)
            except CoreError as exc:
                self.report(exc)

    def _fragment_states(self) -> list[FileState]:
        """Fragments included by the current document (the root or a part)."""
        return [state for state in self.prepared.values() if state.kind == "fragment" and state.owner is self.root]

    # ------------------------------------------------------------------
    # Static evaluation, include, import
    # ------------------------------------------------------------------

    def _static_scope(self, state: FileState) -> GlobalScope:
        """Names allowed in static paths (decision 50, 10.2): header parameters of the
        file with the command and of the root document, parameters of the project
        (bare and as ``project.*``)."""
        scope = self.interp.new_globals()
        for owner in (state, self.root):
            if owner is None:
                continue
            for name, value in (owner.loaded.header.data.get("params") or {}).items():
                if isinstance(name, str) and name not in scope.definitions:
                    scope.define_value(name, from_data(value), None)
        project = self.options.project
        if project is not None:
            descriptive = self.interp.new_globals()
            for name, (value, _span) in project.params.items():
                descriptive.define_value(name, value, None)
                if name not in scope.definitions:
                    scope.define_value(name, value, None)
            scope.define_value("project", ModuleValue("project", descriptive), None)
        return scope

    def _static(self, node: ast.expr, args: PyArgs, state: FileState) -> Any:
        try:
            return self.interp.eval(node, Env(self._static_scope(state)), args.fragment)
        except CoreError as exc:
            if exc.diagnostic.code == "P2201":
                raise core_error("P2612", args.fragment.span_of(node),
                                 name=str(exc.diagnostic.args.get("name"))) from None
            raise

    def _prepare_include(self, node: N.Command, ctx: _Ctx, *, deferred: bool) -> FileState | None:
        """Load a fragment for ``|include`` and collect its definitions."""
        args = node.args
        state = ctx.state
        if args is None:
            return None
        call = args.call
        path_node = call.args[0] if call.args else args.keyword("path")
        key_node = args.keyword("key")
        part = self._static(args.keyword("part"), args, state) if args.keyword("part") is not None else None
        if key_node is not None:
            # A key of the project key map (9.3): "file" or "file#part", from the project root.
            if path_node is not None or part is not None:
                raise core_error("P7114", args.span)
            key = self._static(key_node, args, state)
            found, part = self._key_path(key, args.fragment.span_of(key_node), include=True)
            path_text = to_str(key)
            path = self.loader.find(found, "fragment")
        else:
            if path_node is None:
                raise core_error("P2609", args.span, command="include", problem="a path is required")
            path_text = self._static(path_node, args, state)
            if not isinstance(path_text, str):
                raise core_error("P2609", args.span, command="include", problem="the path must be a string")
            path = self.loader.find(self.loader.resolve(path_text, state.loaded.source, args.span), "fragment")
        namespace = self._static(args.keyword("ns"), args, state) if args.keyword("ns") is not None else None
        rename_value = self._static(args.keyword("rename"), args, state) if args.keyword("rename") is not None else {}
        if path in self.include_stack:
            chain = " -> ".join(self.loader.display_name(p) for p in [*self.include_stack, path])
            raise core_error("P2615", args.span, chain=chain)
        # The include frame is active while the fragment is parsed, so its
        # syntax errors show where it was included.
        self.frames.append(("include", node.span, ""))
        try:
            loaded = self.loader.load(path, args.span)
        finally:
            self.frames.pop()
        if loaded.header.kind != "fragment":
            raise core_error("P2616", args.span, path=path_text, kind=loaded.header.kind, expected="fragment")
        self._record_inclusion("include", node, path, ns=namespace if isinstance(namespace, str) else None,
                               part=to_str(part) if part is not None else None)
        scope = self.interp.new_globals(parent=self.root.scope if self.root else None)
        fragment = FileState(loaded, scope, Program(self.interp, scope), "fragment",
                             frame=("include", node.span, ""),
                             namespace=namespace if isinstance(namespace, str) else None,
                             rename={str(k): str(v) for k, v in (rename_value or {}).items()},
                             owner=self.root)
        self.states_by_source[id(loaded.source)] = fragment
        given = {kw.arg: (kw.value, args.fragment, ctx.env) for kw in call.keywords
                 if kw.arg is not None and kw.arg not in _INCLUDE_ARGS}
        blocks = self._select_part(loaded, part, args) if part is not None else loaded.document.children
        fragment_blocks = blocks
        self.include_stack.append(path)
        self.frames.append(fragment.frame)  # type: ignore[arg-type]
        try:
            self._define_header(fragment, given)
            self._collect(fragment_blocks, fragment, in_if=False, local=False)
        finally:
            self.frames.pop()
            self.include_stack.pop()
        fragment.blocks = fragment_blocks  # type: ignore[attr-defined]
        if deferred and fragment.exports:
            self.report(core_error("P2610", args.span))
        return fragment

    def _select_part(self, loaded: LoadedFile, part: Any, args: PyArgs) -> list[Any]:
        """Children of ``|part("name"):`` in a fragment (9.3, 10.2)."""
        for block in _walk_blocks(loaded.document.children):
            if isinstance(block, N.Command) and block.name == "part" and block.args is not None \
                    and block.args.positional:
                first = block.args.positional[0]
                if isinstance(first, ast.Constant) and first.value == part:
                    return block.children
        raise core_error("P2618", args.span, part=to_str(part), path=self.loader.display_name(loaded.path))

    # --- parts of a compound document (10.7) --------------------------------------------

    def _prepare_part(self, node: N.Command, ctx: _Ctx | None) -> FileState:
        """Load a part ``|document(path, scope=…, params=…, page=…)`` and collect its definitions.

        A part is a full document: its own scope (above it the styles and
        the project, not the root document), parameters, ``doc``, fragments
        and exports.  ``styles`` and ``structure`` of its header are ignored
        (P7117): the styles and the structure settings are those of the root
        document.

        Args:
            node: the ``|document`` command.
            ctx: ``None`` for a part of the top level (prepared before the
                actions; ``scope=`` is static, ``params=`` is evaluated in the
                root document); the evaluation context for a part inside
                ``|if``/``|for`` or with ``when=`` (decision 118): ``scope=``
                and ``params=`` are evaluated there, so a loop variable may
                give each part its own scope and parameters.  The path is
                static in both cases (decision 104).

        Returns:
            The prepared part.
        """
        from primula.evaluate.loader import strip_extension

        root = self.document_root
        assert root is not None
        args: PyArgs | None = node.args
        if args is None:
            raise core_error("P2609", node.span, command="document", problem="a path is required")
        for keyword_node in args.call.keywords:
            if keyword_node.arg not in _DOCUMENT_ARGS:
                raise core_error("P2609", args.fragment.span_of(keyword_node), command="document",
                                 problem=f"unknown argument '{keyword_node.arg}'")
        path_node = args.call.args[0] if args.call.args else args.keyword("path")
        if path_node is None or len(args.call.args) > 1:
            raise core_error("P2609", args.span, command="document", problem="one path is required")
        path_text = self._static(path_node, args, root)
        if not isinstance(path_text, str):
            raise core_error("P2609", args.span, command="document", problem="the path must be a string")
        path = self.loader.find(self.loader.resolve(path_text, root.loaded.source, args.span), None)
        scope_node = args.keyword("scope")
        if scope_node is None:
            scope_value: Any = nfkc(strip_extension(path.name))
        elif ctx is None:
            scope_value = self._static(scope_node, args, root)
        else:
            scope_value = self.interp.eval(scope_node, ctx.env, args.fragment)
        if not isinstance(scope_value, str) or not _part_scope_name(scope_value) or scope_value in self.part_scopes:
            raise CoreError(error("P7118", args.span, scope=to_str(scope_value)).hint("help.part_scope"))
        self.part_scopes.add(scope_value)
        if path in self.include_stack:
            chain = " -> ".join(self.loader.display_name(p) for p in [*self.include_stack, path])
            raise core_error("P2615", args.span, chain=chain)
        self.frames.append(("document", node.span, ""))
        try:
            loaded = self.loader.load(path, args.span)
        finally:
            self.frames.pop()
        if loaded.header.kind != "document":
            raise core_error("P2616", args.span, path=path_text, kind=loaded.header.kind, expected="document")
        self._record_inclusion("document", node, path, scope=scope_value)
        for key in ("styles", "structure"):
            if key in loaded.header.data:
                self.sink.emit(warning("P7117", loaded.header.value_span((key,), key=True) or args.span, key=key))
        values: dict[str, Any] = {}
        params_node = args.keyword("params")
        if params_node is not None:
            given = self.interp.eval(params_node, ctx.env if ctx is not None else Env(root.scope), args.fragment)
            if isinstance(given, Record):
                given = dict(given.fields.items())
            if not isinstance(given, (PDict, dict)) or not all(isinstance(k, str) for k in given):
                raise core_error("P2609", args.fragment.span_of(params_node), command="document",
                                 problem="params= must be a mapping of parameter names to values")
            values = {nfkc(k): v for k, v in given.items()}
        scope = self.interp.new_globals(parent=self.styles_scope)
        part = FileState(loaded, scope, Program(self.interp, scope), "document", frame=("document", node.span, ""),
                         part_scope=scope_value)
        self.states_by_source[id(loaded.source)] = part
        # Identical style definitions of several parts are allowed (10.7).
        self.registry.allow_identical = True
        saved = self.root, self.header_data
        self.root = part
        self.header_data = loaded.header.data if isinstance(loaded.header.data, dict) else {}
        self.include_stack.append(path)
        self.frames.append(part.frame)  # type: ignore[arg-type]
        try:
            span = args.fragment.span_of(params_node) if params_node is not None else args.span
            self._define_header(part, None, values=values, values_span=span)
            self._define_doc(part)
            self._collect(loaded.document.children, part, in_if=False, local=False)
            self._merge_exports()
        finally:
            self.frames.pop()
            self.include_stack.pop()
            self.root, self.header_data = saved
        return part

    def _expand_part(self, block: N.Command, ctx: _Ctx, out: list[Any], keep: tuple[bool, str | None, bool]) -> None:
        """Evaluate a part: its blocks in its own scope, as a ``document`` environment (10.7).

        The node keeps ``scope`` and ``page`` in its arguments: the structure
        phase numbers the part in its own scope and prefixes its IDs with
        ``scope:``; the pages phase starts it on a new page.
        """
        part = self.parts.get(id(block))
        if part is None:
            if id(block) not in self.deferred_parts:
                return  # the preparation failed and was reported
            # A part inside |if/|for or with when= (decision 118): prepared now;
            # its actions run at once (the root's actions have already run).
            before = len(self.actions)
            try:
                part = self._prepare_part(block, ctx)
                for program, action, owner in self.actions[before:]:
                    self.interp.meter.begin()
                    self._with_frame(owner, lambda: program.run_action(action, self.sink))
            except CoreError as exc:
                self.report(exc)
                return
            finally:
                del self.actions[before:]
        # Several parts may come from one file: has() and markup() find the
        # part being expanded by its source.
        self.states_by_source[id(part.loaded.source)] = part
        page = None
        if block.args is not None and block.args.keyword("page") is not None:
            page = self.interp.eval(block.args.keyword("page"), ctx.env, block.args.fragment)
        saved = self.root, self.header_data
        self.root = part
        self.header_data = part.loaded.header.data if isinstance(part.loaded.header.data, dict) else {}
        self.include_stack.append(part.loaded.path)
        self.frames.append(part.frame)  # type: ignore[arg-type]
        try:
            children = self._expand_blocks(part.loaded.document.children, _Ctx(part, Env(part.scope)))
        finally:
            self.frames.pop()
            self.include_stack.pop()
            self.root, self.header_data = saved
        shift = self._level_shift(block, ctx, "document")
        self._shift_headings(children, shift)
        keywords: dict[str, Any] = {"scope": part.part_scope}
        if shift:
            keywords["level_shift"] = shift  # the structure phase nests the part's numbering (П3)
        if page is not None:
            keywords["page"] = page
        args = EArgs(block.span, [self.loader.display_name(part.loaded.path)], keywords)
        node = N.Command(block.span, "document", block.name_span, args, "env", [], children)  # type: ignore[arg-type]
        out.append(self._mark(node, keep))

    def _level_shift(self, block: Any, ctx: _Ctx, command: str) -> int:
        """``level_shift=`` of ``|include``/``|document``: an integer 0…5 (П3), 0 without it."""
        args = getattr(block, "args", None)
        node = args.keyword("level_shift") if isinstance(args, PyArgs) else None
        if node is None:
            return 0
        value = self.interp.eval(node, ctx.env, args.fragment)
        if isinstance(value, bool) or not isinstance(value, (int, Decimal)) or value != int(value) \
                or not 0 <= int(value) <= 5:
            raise core_error("P2609", args.fragment.span_of(node), command=command,
                             problem="level_shift= must be an integer from 0 to 5")
        return int(value)

    def _shift_headings(self, blocks: list[Any], shift: int) -> None:
        """Move the headings of inserted content ``shift`` levels down (П3).

        The numbers of ``<`` and ``level=`` are already applied to the
        evaluated nodes (fresh copies for every insertion).  A level above 6
        is P2636 and stays 6; clauses are counted from the heading and are
        not changed.
        """
        if not shift:
            return
        for node in iter_tree(blocks):
            if isinstance(node, N.Heading):
                node.level += shift
                if node.level > 6:
                    self.report(core_error("P2636", node.span, level=node.level, shift=shift))
                    node.level = 6

    def _import(self, node: Any, state: FileState) -> None:
        """``|import("path", names…, alias=…)`` (10.3, decision 52)."""
        args: PyArgs | None = node.args
        if args is None or not args.call.args:
            raise core_error("P2609", node.span, command="import", problem="a path is required")
        path_text = self._static(args.call.args[0], args, state)
        if not isinstance(path_text, str):
            raise core_error("P2609", args.span, command="import", problem="the path must be a string")
        names = [self._static(arg, args, state) for arg in args.call.args[1:]]
        alias = self._static(args.keyword("alias"), args, state) if args.keyword("alias") is not None else None
        path: Path | None = None
        if path_text.startswith("std/"):
            # A built-in code module of the standard library (std/math, library 9).
            values = std_module(self.library, path_text)
            if values is None:
                raise core_error("P2625", args.span, name=path_text)
            scope = self.interp.new_globals()
            for name, value in values.items():
                scope.define_value(name, value, None)
            module = _BuiltinModule(scope)
            path = Path(path_text)
        else:
            path = self.loader.find(self.loader.resolve(path_text, state.loaded.source, args.span), "module")
            module = self.modules.get(path)
        if module is None:
            if path in self.include_stack:
                chain = " -> ".join(self.loader.display_name(p) for p in [*self.include_stack, path])
                raise core_error("P2615", args.span, chain=chain)
            loaded = self.loader.load(path, args.span)
            if loaded.header.kind != "module":
                raise core_error("P2616", args.span, path=path_text, kind=loaded.header.kind, expected="module")
            scope = self.interp.new_globals()
            module = FileState(loaded, scope, Program(self.interp, scope), "module",
                               frame=("import", node.span, ""))
            self.modules[path] = module
            self.states_by_source[id(loaded.source)] = module
            self.include_stack.append(path)
            self.frames.append(module.frame)  # type: ignore[arg-type]
            # A module defines no styles while it loads (decision 59).
            saved_layer, self.registry.current = self.registry.current, None
            try:
                self._check_module(loaded)
                before = len(self.actions)
                self._collect(loaded.document.children, module, in_if=False, local=False)
                # A module is evaluated once, when it is loaded (10.3).
                for program, action, owner in self.actions[before:]:
                    program.run_action(action, self.sink)
                del self.actions[before:]
            finally:
                self.registry.current = saved_layer
                self.frames.pop()
                self.include_stack.pop()
        span = node.span
        if names:
            for name in names:
                if not isinstance(name, str) or name.startswith("_") or name not in module.scope.definitions:
                    self.report(core_error("P2624", span, name=to_str(name), module=path_text))
                    continue
                if name in RESERVED_NAMES:
                    # A macro named like a built-in command stays behind the namespace (decision 142).
                    self.report(core_error("P1235", span, name=name))
                    continue
                state.scope.define(name, lambda n=name, m=module: m.scope.lookup(n, span), span)
            return
        # The base of the file name without the extension and the
        # sub-extension (10.3): lib/договір.m.prml -> договір.
        namespace = alias if alias is not None else nfkc(strip_extension(path.name))
        if not isinstance(namespace, str) or not is_identifier(namespace) or namespace in RESERVED_NAMES:
            raise CoreError(error("P2622", span, name=to_str(namespace)).hint("help.import_alias"))
        state.scope.define(namespace, lambda: ModuleValue(namespace, module.scope), span)

    def _check_module(self, loaded: LoadedFile) -> None:
        """A module contains only definitions (decision 52)."""
        for block in loaded.document.children:
            allowed = isinstance(block, (N.DefBlock, N.CodeBlock, N.Comment, N.BlankLine)) or (
                isinstance(block, N.Command) and block.name in ("let", "import") and block.form == "bare")
            if not allowed:
                self.report(core_error("P2623", block.span))

    # ------------------------------------------------------------------
    # Built-in functions of the document: has, markup
    # ------------------------------------------------------------------

    def _has(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> bool:
        """``has(name)`` — product feature check (9.2, decision 53)."""
        if len(args) != 1 or kwargs or not isinstance(args[0], str):
            raise core_error("P2322", span, function="has", problem="expected one feature name")
        document = self._document_of(span)
        if not document.scope.has("features"):
            return False
        features = document.scope.lookup("features", span)
        if not isinstance(features, (PList, tuple)) or not all(isinstance(f, str) for f in features):
            raise core_error("P2626", span)
        return args[0] in features

    def _fn_param(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Any:
        """``param(name, default=None)`` — a parameter of the root document, also inside a module (decision 144)."""
        if not 1 <= len(args) <= 2 or set(kwargs) - {"default"} or not isinstance(args[0], str):
            raise core_error("P2322", span, function="param", problem="expected a name (a string) and an optional default")
        default = args[1] if len(args) == 2 else kwargs.get("default")
        name = nfkc(args[0])
        if name not in self.root_params or self.document_root is None:
            return default
        return self.document_root.scope.lookup(name, span)

    def _fn_collect(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Content:
        """``collect(name, value)`` — add a value to the collection ``name`` of the document (decision 143).

        The value is frozen.  The result is empty content, so the call can stand in the text: ``|(collect("n", x))``.
        """
        if len(args) != 2 or kwargs or not isinstance(args[0], str) or not args[0]:
            raise core_error("P2322", span, function="collect", problem="expected a name (a string) and a value")
        self.collections.setdefault(args[0], []).append(freeze(args[1]))
        return content_inline([])

    def _fn_collected(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> PList:
        """``collected(name)`` — the values of the collection after the whole document (decision 143).

        The document is evaluated twice when this is called: the first pass collects, the second one sees
        the finished collections (``[]`` in the first pass, whose output and messages are dropped).
        """
        if len(args) != 1 or kwargs or not isinstance(args[0], str) or not args[0]:
            raise core_error("P2322", span, function="collected", problem="expected a name (a string)")
        self.collected_used = True
        seed = self.options.collected or {}
        return freeze(PList(list(seed.get(args[0], ()))))

    def _document_of(self, span: Any) -> FileState:
        """The document (root or part) of the file at ``span``; the current one otherwise."""
        state = self.states_by_source.get(id(resolve(span).source))
        if state is not None and state.kind == "document":
            return state
        if state is not None and state.owner is not None:
            return state.owner
        assert self.root is not None
        return self.root

    def _markup(self, interp: Any, args: list[Any], kwargs: dict[str, Any], span: Any) -> Content:
        """``markup(text)`` — parse and evaluate markup from a string (4.2)."""
        if len(args) != 1 or kwargs or not isinstance(args[0], str):
            raise core_error("P2322", span, function="markup", problem="expected one string")
        call = resolve(span)
        source = SourceFile.from_text("<markup>", args[0])
        header = Header(source, kind="fragment")
        state = self.states_by_source.get(id(call.source), self.root)
        if state is None:
            # The console without a file has no document to evaluate markup in.
            raise core_error("P2322", span, function="markup", problem="needs a document: open the console with a file")
        self.frames.append(("call", call, "markup"))
        try:
            document = parse(header, self.sink, organize=False)
            blocks = self._expand_blocks(document.children, _Ctx(state, Env(state.scope)))
        finally:
            self.frames.pop()
        return content_blocks(blocks)

    # ------------------------------------------------------------------
    # Macros
    # ------------------------------------------------------------------

    def _make_macro(self, block: N.DefBlock, closure: Env | GlobalScope, state: FileState) -> Macro:
        function = self.interp.make_function(block.func.node, closure, block.func.fragment)
        macro = Macro(block.name, None, definition=block, closure=closure, file=state)  # type: ignore[arg-type]
        macro.function = function  # type: ignore[attr-defined]
        macro.impl = lambda interp, args, kwargs, span, m=macro: self.call_macro(m, args, kwargs, span, None)
        return macro

    def call_macro(self, macro: Macro, args: list[Any], kwargs: dict[str, Any], span: Any,
                   body: Content | None) -> Content:
        """Call a macro (decision 48): bind arguments, evaluate the body.

        Args:
            macro: the macro.
            args: positional arguments.
            kwargs: keyword arguments.
            span: the call site.
            body: content passed with ``{…}`` or an environment, if any.

        Returns:
            The evaluated body as block content.
        """
        function: Function = macro.function  # type: ignore[attr-defined]
        params = function.node.args
        names = {arg.arg for arg in [*params.posonlyargs, *params.args, *params.kwonlyargs]}
        if body is not None:
            if "body" not in names and params.kwarg is None:
                raise core_error("P2606", span, name=macro.name)
            kwargs = {**kwargs, "body": body}
        closure = function.closure
        env = Env(closure if isinstance(closure, GlobalScope) else closure.globals,
                  None if isinstance(closure, GlobalScope) else closure, None)
        call_span = resolve(span)
        self.interp.meter.enter(call_span)
        self.frames.append(("macro", call_span, macro.name))
        try:
            self.interp._bind(function, args, kwargs, env, call_span)
            blocks = self._expand_blocks(macro.definition.children,
                                         _Ctx(macro.file, env, local=True))
        finally:
            self.frames.pop()
            self.interp.meter.leave()
        return content_blocks(blocks)

    # ------------------------------------------------------------------
    # Phase 3: markup
    # ------------------------------------------------------------------

    def _expand_blocks(self, blocks: list[Any], ctx: _Ctx) -> list[Any]:
        out: list[Any] = []
        for block in blocks:
            # A top-level block is one evaluation for the time limit (12.8);
            # inside a macro call (depth > 0) the clock keeps running.
            self.interp.meter.begin()
            try:
                self._expand_block(block, ctx, out)
            except CoreError as exc:
                self.report(exc)
        return out

    def _when(self, args: PyArgs | None, ctx: _Ctx, node: Any) -> tuple[bool, str | None]:
        """Evaluate ``when=`` (9.2, decision 29): a boolean expression."""
        if args is None:
            return True, None
        condition = args.keyword("when")
        if condition is None:
            return True, None
        value = self.interp.eval(condition, ctx.env, args.fragment)
        if not isinstance(value, bool):
            raise CoreError(error("P2611", args.fragment.span_of(condition), type=type_name(value))
                            .hint("help.when_bool"))
        text = args.fragment.segment(condition)
        self.conditions.append((text, value, args.fragment.span_of(condition)))
        return value, text

    def _eargs(self, args: PyArgs | None, ctx: _Ctx, *, skip: tuple[str, ...] = ("when",)) -> EArgs | None:
        """Evaluate command arguments (``when`` excluded)."""
        if args is None:
            return None
        keywords = [kw for kw in args.call.keywords if kw.arg not in skip]
        positional, named = self.interp.eval_arguments(args.call.args, keywords, ctx.env, args.fragment)
        return EArgs(args.span, positional, named, args)

    def _keep(self, node: Any, ctx: _Ctx) -> tuple[bool, str | None, bool]:
        """``(keep, condition text, truth)``; ``--review`` keeps a false condition (9.2)."""
        keep, condition = self._when(getattr(node, "args", None), ctx, node)
        if not keep and self.options.review:
            return True, condition, False
        if not keep:
            self._record_excluded([node], condition or "", self.conditions[-1][2])
        return keep, condition, keep

    def _record_excluded(self, nodes: list[Any], condition: str, span: Span) -> None:
        """Remember literal IDs of excluded parsed nodes (decision 75).

        A computed ID is unknown without evaluation; a reference to it is
        reported as an unknown target.
        """
        for node in iter_tree(nodes):
            args = getattr(node, "args", None)
            if isinstance(args, PyArgs):
                value = args.keyword("id")
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    part = self.root.part_scope if self.root is not None else None
                    key = f"{part}:{value.value}" if part else value.value
                    self.excluded_ids.setdefault(key, (condition, span))

    def _skipped_branches(self, branches: list[Any], taken: Any) -> None:
        """Record IDs of the ``|if`` branches not taken (decision 75)."""
        for branch in branches:
            if branch is taken:
                continue
            cond = branch.cond if branch.cond is not None else branches[0].cond
            if cond is None:
                continue
            text = cond.fragment.segment(cond.node)
            nested = branch.children if hasattr(branch, "children") else branch.body
            self._record_excluded(nested, text, cond.fragment.span_of(cond.node))

    def _mark(self, node: Any, keep_condition: tuple[bool, str | None, bool]) -> Any:
        keep, condition, truth = keep_condition
        if condition is not None:
            node.condition = condition  # type: ignore[attr-defined]
            if self.options.review:
                node.review = (f"when: {condition}", truth)  # type: ignore[attr-defined]  # 9.2, decision 116
        return node

    def _expand_block(self, block: Any, ctx: _Ctx, out: list[Any]) -> None:
        if isinstance(block, (N.BlankLine, N.Verbatim)):
            out.append(block)
            return
        if isinstance(block, (N.Comment, N.CommentBlock)):
            return
        if isinstance(block, N.CodeBlock):
            if ctx.local and block.code is not None:
                self.interp.exec_block(block.code.module.body, ctx.env, block.code.fragment)
            return
        if isinstance(block, N.DefBlock):
            if ctx.local:
                ctx.env.assign(block.name, self._make_macro(block, ctx.env, ctx.state))
            return
        if isinstance(block, N.IfBlock):
            if self.options.review:
                if _markup_only(block.branches):
                    self._review_if(block, ctx, out)
                    return
                self.sink.emit(warning("P9106", block.span))
            taken = None
            for branch in block.branches:
                if branch.cond is None or self.interp.truthy(
                        self.interp.eval(branch.cond.node, ctx.env, branch.cond.fragment)):
                    taken = branch
                    out.extend(self._expand_blocks(branch.children, ctx))
                    break
            self._skipped_branches(block.branches, taken)
            return
        if isinstance(block, N.ForBlock):
            iterable = self.interp.eval(block.loop.node.iter, ctx.env, block.loop.fragment)
            for item in self.interp.iterate(iterable, block.loop.span):
                env = Env(ctx.env.globals, ctx.env, None)
                self.interp.assign(block.loop.node.target, item, env, block.loop.fragment)
                out.extend(self._expand_blocks(block.children, replace(ctx, env=env, local=True)))
            return
        if isinstance(block, N.Command):
            self._expand_command(block, ctx, out)
            return
        if isinstance(block, N.Paragraph):
            self._expand_paragraph(block, ctx, out)
            return

        keep = self._keep(block, ctx)
        if not keep[0]:
            return
        if isinstance(block, N.TableRow):
            cells = []
            for cell in block.cells:
                new_cell = replace(cell, args=self._eargs(cell.args, ctx))
                new_cell.body = self._cell_inlines(cell.body, replace(ctx, container="cell"), cell.span, new_cell)
                cells.append(new_cell)
            out.append(self._mark(replace(block, args=self._eargs(block.args, ctx), cells=cells), keep))
            return
        new = replace(block, args=self._eargs(block.args, ctx))
        if isinstance(block, N.Heading) and new.args is not None and "level" in new.args.keywords:
            new.level = self._heading_level(new.args, block)
        if isinstance(block, N.StyleBlock):
            new.style = self._style_ref(block.style, ctx)
        if hasattr(block, "body") and block.body:
            new.body = self._expand_inlines(block.body, ctx, block.span)
        if getattr(block, "form", None) == "env":
            new.children = self._expand_blocks(block.children, replace(ctx, container=None))
        out.append(self._mark(new, keep))

    def _review_if(self, block: N.IfBlock, ctx: _Ctx, out: list[Any]) -> None:
        """``--review``: every branch of a markup-only ``|if`` with its condition (9.2, decision 116)."""
        taken_found = False
        taken = None
        for index, branch in enumerate(block.branches):
            truth = False
            if not taken_found and (branch.cond is None or self.interp.truthy(
                    self.interp.eval(branch.cond.node, ctx.env, branch.cond.fragment))):
                truth = taken_found = True
                taken = branch
            label = _branch_label(block.branches, index)
            blocks = [b for b in self._expand_blocks(branch.children, ctx)]
            first = True
            for produced in blocks:
                if isinstance(produced, N.BlankLine):
                    out.append(produced)
                    continue
                produced.review = (label, truth, first)  # type: ignore[attr-defined]
                if not truth:
                    produced.condition = label  # type: ignore[attr-defined]  # a target here warns (P4303)
                first = False
                out.append(produced)
        # IDs of the branches not taken: references resolve with a warning (decision 75).
        self._skipped_branches(block.branches, taken)

    @staticmethod
    def _heading_level(args: EArgs, block: N.Heading) -> int:
        """``|<(level=N)``: the level is an ordinary expression (3.2, 5.2; decision 114).

        Combining ``level=`` with several ``<`` is a syntax error found by
        the parser (P1244); here the value must be an integer 1-6 (P4212).
        """
        value = args.keywords["level"]
        from primula.core.numbers import as_integer

        level = as_integer(value) if not isinstance(value, bool) else None
        if level is None or not 1 <= level <= 6:
            raise core_error("P4212", args.span, value=to_repr(value))
        return level

    def _expand_paragraph(self, block: N.Paragraph, ctx: _Ctx, out: list[Any]) -> None:
        # A paragraph that is exactly one |(expr) giving block content is
        # replaced by the blocks (macro bodies: |(body), decision 48).
        meaningful = [n for n in block.body if not (isinstance(n, N.Comment)
                                                    or isinstance(n, N.Text) and not n.value.strip())]
        if len(meaningful) == 1 and isinstance(meaningful[0], N.Expr) and meaningful[0].expr is not None:
            value = self.interp.eval(meaningful[0].expr.node, ctx.env, meaningful[0].expr.fragment)
            if isinstance(value, Content) and value.kind == "blocks":
                out.extend(value.nodes)
                return
            inlines = self._value_inlines(value, meaningful[0].span)
        else:
            inlines = self._expand_inlines(block.body, ctx, block.span)
        only_control = all(isinstance(n, (N.InlineIf, N.InlineFor, N.Comment)) or
                           isinstance(n, N.Text) and not n.value.strip() for n in block.body)
        if not inlines and (only_control or not block.body):
            return  # empty after evaluation (decision 21)
        out.append(replace(block, body=inlines))

    # --- commands --------------------------------------------------------

    def _expand_command(self, block: N.Command, ctx: _Ctx, out: list[Any]) -> None:
        name = block.name
        if name in ("let", "export", "import"):
            if ctx.local and name == "let":
                self._local_let(block.args, ctx)
            return
        if name == "include":
            self._expand_include(block, ctx, out)
            return
        keep = self._keep(block, ctx)
        if not keep[0]:
            return
        if name == "document":
            self._expand_part(block, ctx, out, keep)
            return
        if name == "part":
            out.extend(self._expand_blocks(block.children, ctx))
            return
        if name == "parallel":
            self._expand_parallel(block, ctx, out)
            return
        if name == "segment" and ctx.container == "parallel":
            self._expand_segment(block, ctx, out)
            return
        if name in ("segment", "track"):
            where = "outside_parallel" if name == "segment" else "outside_segment"
            raise CoreError(error("P5302", block.name_span, command=name, where=Key("parallel." + where))
                            .hint("help.parallel"))
        if name == "call" or not _is_builtin(name):
            self._call_command(block, ctx, out, block_form=True)
            return
        new = replace(block, args=self._eargs(block.args, ctx))
        if name in ("img", "figure"):
            self._image_path(new, ctx)
        if name == "cell" and block.form == "env" and self._single_cell_value(block.children, ctx, new):
            out.append(self._mark(new, keep))
            return
        if block.body:
            if name == "cell":
                new.body = self._cell_inlines(block.body, ctx, block.span, new)
            else:
                new.body = self._expand_inlines(block.body, ctx, block.span)
        if block.form == "env":
            container = name if name in ("table", "row") else None
            new.children = self._expand_blocks(block.children, replace(ctx, container=container))
        if name == "table" and new.args is not None and "data" in new.args.keywords:
            # |table(data=…) (П4): rows from data, then the rows of the body (totals, |=).
            new.children = self._data_rows(new, block.span) + list(new.children or [])
            new.form = "env"
        out.append(self._mark(new, keep))

    # --- parallel tracks (7.7, decision 134) ----------------------------------

    def _expand_parallel(self, block: N.Command, ctx: _Ctx, out: list[Any]) -> None:
        """``|parallel(…):`` — evaluate the segments and replace the environment by tables (7.7).

        The arguments give a :class:`~primula.parallel.model.ParallelSpec`;
        the content is evaluated with the container ``parallel`` (segments,
        control constructs, code, includes, page breaks); anything else
        is P5303.  :func:`~primula.parallel.build.build_tables` makes the
        tables.
        """
        args = self._eargs(block.args, ctx)
        where = args.span if args is not None else block.name_span
        spec = parallel_model.parallel_spec(dict(args.keywords) if args else {}, list(args.positional) if args else [],
                                            where)
        if block.form != "env":
            raise parallel_model.problem(block.span, "|parallel", "env_form", "|parallel(…):")
        for track_id in spec.unsupported:
            track = spec.track(track_id)
            self.sink.emit(warning("P5308", where, lang=track.fields["lang"], track=track_id))
        self.parallel_stack.append(spec)
        try:
            items = self._expand_blocks(block.children, replace(ctx, container="parallel"))
        finally:
            self.parallel_stack.pop()
        content: list[Any] = []
        for item in items:
            if isinstance(item, EvaluatedSegment) or isinstance(item, N.Command) and item.name in ("page", "newpage"):
                content.append(item)
            elif not isinstance(item, N.BlankLine):
                self.report(core_error("P5303", item.span, what=_block_label(item), container="parallel"))
        out.extend(build_tables(spec, content, block.span, self.sink))

    def _expand_segment(self, block: N.Command, ctx: _Ctx, out: list[Any]) -> None:
        """``|segment`` inside ``|parallel`` (7.7): its track blocks or its full-width blocks."""
        spec = self.parallel_stack[-1]
        args = self._eargs(block.args, ctx)
        where = args.span if args is not None else block.name_span
        checked = parallel_model.segment_args(dict(args.keywords) if args else {},
                                              list(args.positional) if args else [], where)
        if checked.id is not None:
            first = self.segment_ids.get(checked.id)
            if first is not None:
                self.report(CoreError(error("P5306", where, id=checked.id).note("note.first_definition", first)))
            else:
                self.segment_ids[checked.id] = where
        segment = EvaluatedSegment(block.span, id=checked.id, full=checked.full, keep=checked.keep,
                                   status=checked.status, parity=checked.parity)
        tracks = [c for c in block.children if isinstance(c, N.Command) and c.name == "track"]
        if checked.full:
            for child in tracks:
                self.report(CoreError(error("P5302", child.name_span, command="track",
                                            where=Key("parallel.in_full_width")).hint("help.parallel")))
            others = [c for c in block.children if c not in tracks]
            segment.blocks = self._expand_blocks(others, replace(ctx, container=None))
            self._check_segment_content(segment.blocks)
        else:
            record = parallel_model.segment_record(checked)
            for child in block.children:
                if isinstance(child, (N.BlankLine, N.Comment, N.CommentBlock)):
                    continue
                if child not in tracks:
                    self.report(core_error("P5303", child.span, what=_block_label(child), container="segment"))
                    continue
                try:
                    self._expand_track(child, spec, segment, record, ctx)
                except CoreError as exc:
                    self.report(exc)
            self._check_revs(spec, segment)
        out.append(segment)

    def _fragment_text(self, node: Any) -> tuple[str, int, list[Any]] | None:
        """The source text, body start and parsed blocks of the fragment of an ``|include`` (rev hashes)."""
        state = self.prepared.get(id(node))
        if state is None:
            return None
        loaded = state.loaded
        return loaded.source.text, loaded.header.body_start, list(loaded.document.children)

    def _check_revs(self, spec: Any, segment: EvaluatedSegment) -> None:
        """``rev`` of the track blocks of a segment (7.7): P5307, P5320, P5321; status labels in ``--review``."""
        primary = spec.primary
        name = segment.id or "—"
        for track_id, args in segment.track_args.items():
            source = segment.sources[track_id].args  # the parsed arguments (PyArgs)
            node = source.keyword("rev") if source is not None else None
            where = source.fragment.span_of(node) if node is not None else segment.track_spans[track_id]
            if args.rev is not None:
                parsed = parallel_rev.parse_rev(args.rev)
                if track_id == primary or parsed is None:
                    self.report(core_error("P5307", where, track=track_id,
                                           problem=Key("parallel.rev_primary" if track_id == primary
                                                       else "parallel.rev_format")))
                else:
                    now = segment.hashes.get(primary)
                    if now is not None and parsed[0] != now:
                        segment.stale[track_id] = True
                        self.sink.emit(warning("P5320", where, segment=name, track=track_id, rev=parsed[0], now=now)
                                       .note("note.primary_track", segment.track_spans[primary]))
                    if parsed[1] != segment.hashes[track_id]:
                        segment.changed[track_id] = True
                        self.sink.emit(warning("P5321", where, segment=name, track=track_id, rev=parsed[1],
                                               now=segment.hashes[track_id]))
            status = args.status or segment.status
            if self.options.review and status is not None and track_id != primary:
                # --review shows the status of a track block at the start of its cell (14.1).
                outdated = segment.stale.get(track_id) or segment.changed.get(track_id)
                span = segment.track_spans[track_id]
                text = f"[{status}{', rev ≠' if outdated else ''}]"
                label = N.StyleBlock(span, N.StyleRef(span, "ReviewLabel"), None, "line", [N.Text(span, text)])
                segment.tracks[track_id].insert(0, label)

    def _expand_track(self, block: N.Command, spec: Any, segment: EvaluatedSegment, record: Any, ctx: _Ctx) -> None:
        """A track block: its blocks in the language of the track, with ``track`` and ``segment`` (7.7)."""
        keep = self._keep(block, ctx)
        args = self._eargs(block.args, ctx)
        where = args.span if args is not None else block.name_span
        checked = parallel_model.track_args(dict(args.keywords) if args else {},
                                            list(args.positional) if args else [], where)
        track = spec.track(checked.track)
        if track is None:
            raise CoreError(error("P5302", where, command=f'track("{checked.track}")',
                                  where=Key("parallel.unknown_track")).hint("help.parallel"))
        if checked.track in segment.tracks:
            raise core_error("P5303", block.span, what=f'|track("{checked.track}")', container="segment")
        segment.track_args[checked.track] = checked
        segment.track_spans[checked.track] = block.span
        segment.tracks[checked.track] = []
        segment.sources[checked.track] = block
        segment.hashes[checked.track] = parallel_rev.block_hash(block, self._fragment_text)
        if not keep[0]:
            return  # excluded by when=: an empty cell without P5301
        env = Env(ctx.env.globals, ctx.env, None)
        env.assign("track", track)
        env.assign("segment", record)
        inner = replace(ctx, env=env, container=None)
        language = track.fields["lang"]
        if language is not None:
            # A language the library does not know falls back to English (P5308 was given).
            self.track_languages.append(language if checked.track not in spec.unsupported else "en")
        try:
            if block.form == "inline":
                inlines = self._expand_inlines(block.body, inner, block.span)
                blocks = [N.Paragraph(block.span, inlines)] if inlines else []
            else:
                blocks = self._expand_blocks(block.children, inner)
        finally:
            if language is not None:
                self.track_languages.pop()
        self._check_segment_content(blocks)
        _tag_track(blocks, checked.track, block, None if track.fields["primary"] else spec.primary)
        segment.tracks[checked.track] = blocks
        # Names in |(…) and literal numbers need the source text (parity="translation", 7.7).
        segment.facts[checked.track] = parallel_parity.source_facts(
            block, blocks, [t.fields["id"] for t in spec.tracks], lambda name: _is_value_name(name, env))

    def _check_segment_content(self, blocks: list[Any]) -> None:
        """P5304: page structure, indexes, nested ``|parallel`` and page-anchored frames in a segment (7.7)."""
        for node in iter_tree(blocks):
            if not isinstance(node, N.Command):
                continue
            args = node.args.keywords if isinstance(node.args, EArgs) else {}
            if node.name in parallel_model.FORBIDDEN or node.name in ("img", "figure", "frame") and (
                    args.get("rel") == "page" or args.get("anchor") == "page"):
                self.report(core_error("P5304", node.name_span, command=node.name))

    def _data_rows(self, table: Any, span: Span) -> list[Any]:
        """Rows of ``|table(data=…, fields=[…], titles=[…])`` (6.2, П4).

        ``data`` is a list of records, dictionaries or lists; ``fields`` —
        the fields by columns (by default all fields of the first record;
        for lists — all items of the first one); ``titles`` — the title row
        (by default the field names; lists without ``titles`` get no title
        row, so ``header=0`` is then needed).  A field missing in a record
        is P5115.  Cells keep their values: the column type formats them as
        for ``|(…)`` in a cell.  The arguments are removed from the node.
        """
        keywords = table.args.keywords
        data = keywords.pop("data")
        fields = keywords.pop("fields", None)
        titles = keywords.pop("titles", None)
        problem = None
        if not isinstance(data, (list, tuple, PList)):
            problem = "data= must be a list of records, dicts or lists"
        items = list(data) if problem is None else []
        mapping = [self._fields_of(item) for item in items]
        if problem is None and any(m is None and not isinstance(item, (list, tuple, PList))
                                   for m, item in zip(mapping, items)):
            problem = "data= must be a list of records, dicts or lists"
        if problem is None and fields is not None and (not isinstance(fields, (list, tuple, PList))
                                                       or not all(isinstance(f, str) for f in fields)):
            problem = "fields= must be a list of field names"
        if problem is None and titles is not None and (not isinstance(titles, (list, tuple, PList))
                                                       or (fields is not None and len(titles) != len(fields))):
            problem = "titles= must be a list with one title per field"
        if problem is not None:
            raise core_error("P2609", table.args.span, command="table", problem=problem)
        if fields is None:
            first = mapping[0] if mapping else None
            fields = list(first) if first is not None else (list(range(len(items[0]))) if items else [])
        rows: list[Any] = []
        if titles is None and mapping and mapping[0] is not None:
            titles = [str(f) for f in fields]
        if titles is not None:
            rows.append(N.TableRow(span, None, [N.Cell(span, None, [N.Text(span, to_str(t))]) for t in titles]))
        for number, (item, fields_of) in enumerate(zip(items, mapping), 1):
            cells = []
            for field_name in fields:
                if fields_of is not None:
                    if field_name not in fields_of:
                        raise core_error("P5115", table.args.span, row=number, field=str(field_name))
                    value = fields_of[field_name]
                else:
                    value = item[field_name] if isinstance(field_name, int) and field_name < len(item) else None
                cell = N.Cell(span, None, [])
                if isinstance(value, Content):
                    cell.body = self._content_inline(value, span, None)
                else:
                    cell.cell_value = value
                cells.append(cell)
            rows.append(N.TableRow(span, None, cells))
        return rows

    @staticmethod
    def _fields_of(item: Any) -> dict[str, Any] | None:
        """Field name -> value of a record or dictionary; ``None`` for anything else."""
        if isinstance(item, Record):
            return dict(item.fields.items())
        if isinstance(item, (dict, PDict)):
            return {str(k): v for k, v in item.items()}
        return None

    def _image_path(self, node: Any, ctx: _Ctx) -> None:
        """Resolve the image of ``|img``/``|figure`` (``node.image_path``).

        The image is given by exactly one source (P6113): a path relative to
        the file containing the command (10.1); ``key=`` — a key of the
        project key map, its path is relative to the project root (9.3; a key
        with ``#part`` is P7113, a key with a path P7114); ``svg=`` — an SVG
        string computed by code (decision 131); an image value ``img(…)``
        (its options are defaults of the command's arguments).  For an SVG
        string ``image_path`` holds the checked image
        (:class:`~primula.pages.images.ImageInfo`) instead of a path.
        """
        args = node.args
        if args is None:
            return
        keywords = args.keywords
        try:
            if "key" in keywords and args.positional:
                raise core_error("P7114", args.span)
            sources = len(args.positional[:1]) + ("key" in keywords) + ("svg" in keywords)
            value = args.positional[0] if args.positional else None
            if sources > 1 or (sources == 1 and value is not None and not isinstance(value, (str, ImageValue))):
                raise core_error("P6113", args.span, command=node.name)
            if "key" in keywords:
                node.image_path, _part = self._key_path(keywords["key"], args.span, include=False)
            elif "svg" in keywords:
                node.image_path = checked_svg(keywords.pop("svg"), args.span)
            elif isinstance(value, ImageValue):
                fields = value.fields
                for name, option in fields.items():
                    if name not in ("path", "svg"):
                        keywords.setdefault(name, option)
                node.image_path = checked_svg(fields["svg"], args.span) if "svg" in fields \
                    else Path(fields["path"])
            elif isinstance(value, str):
                node.image_path = self.loader.resolve(value, node.span.source, args.span)
        except CoreError as exc:
            self.report(exc)

    def _cell_inlines(self, inlines: list[Any], ctx: _Ctx, span: Span, target: Any) -> list[Any]:
        """Cell content: a single ``|(…)`` gives the cell value (6.8, decision 80).

        The value is kept as ``target.cell_value`` (the table phase formats
        it by the column type) instead of text, so no P2604 is issued; other
        content is expanded as usual.
        """
        meaningful = [n for n in inlines if not (isinstance(n, N.Comment)
                                                 or isinstance(n, N.Text) and not n.value.strip())]
        if len(meaningful) == 1 and isinstance(meaningful[0], N.Expr) and meaningful[0].expr is not None:
            expr = meaningful[0].expr
            value = self.interp.eval(expr.node, ctx.env, expr.fragment)
            if not isinstance(value, Content):
                target.cell_value = value
                return []
            return self._content_inline(value, meaningful[0].span, None)
        return self._expand_inlines(inlines, ctx, span)

    def _single_cell_value(self, children: list[Any], ctx: _Ctx, target: Any) -> bool:
        """``|cell:`` whose body is one paragraph with one ``|(…)``: the cell value."""
        blocks = [b for b in children if not isinstance(b, (N.BlankLine, N.Comment, N.CommentBlock))]
        if len(blocks) != 1 or not isinstance(blocks[0], N.Paragraph):
            return False
        meaningful = [n for n in blocks[0].body if not (isinstance(n, N.Comment)
                                                        or isinstance(n, N.Text) and not n.value.strip())]
        if len(meaningful) != 1 or not isinstance(meaningful[0], N.Expr) or meaningful[0].expr is None:
            return False
        expr = meaningful[0].expr
        value = self.interp.eval(expr.node, ctx.env, expr.fragment)
        if isinstance(value, Content):
            return False
        target.cell_value = value
        target.children = []
        return True

    def _local_let(self, args: PyArgs | None, ctx: _Ctx) -> None:
        """``|let`` inside a ``|for``/``|def`` body: local names (decision 49)."""
        if args is None:
            return
        for keyword_node in args.call.keywords:
            if keyword_node.arg in ("export", "override", None):
                if keyword_node.arg == "export":
                    raise core_error("P2610", args.span)
                continue
            ctx.env.assign(keyword_node.arg, self.interp.eval(keyword_node.value, ctx.env, args.fragment))

    def _expand_include(self, block: N.Command, ctx: _Ctx, out: list[Any]) -> None:
        state = self.prepared.get(id(block))
        if state is None:
            if ctx.local or not isinstance(block, N.Command):
                state = self._prepare_include(block, ctx, deferred=True)
            if state is None:
                return
        blocks = getattr(state, "blocks", state.loaded.document.children)
        self.include_stack.append(state.loaded.path)
        self.frames.append(state.frame)  # type: ignore[arg-type]
        try:
            inserted = self._expand_blocks(blocks, _Ctx(state, Env(state.scope), container=ctx.container))
        finally:
            self.frames.pop()
            self.include_stack.pop()
        if ctx.container in ("table", "row"):
            inserted = [b for b in inserted if self._allowed_in(ctx.container, b)]
        # Blocks inserted into |parallel are checked with the other content of it (7.7).
        self._shift_headings(inserted, self._level_shift(block, ctx, "include"))
        _tag_inclusion(inserted, state)
        out.extend(self._fragment_set(inserted))

    def _fragment_set(self, blocks: list[Any]) -> list[Any]:
        """``|set`` of a fragment acts until the end of the fragment (decision 60).

        The ``|set`` commands at the top level of the inserted blocks are
        removed; the blocks after them get ``set_overrides``.
        """
        result: list[Any] = []
        overrides: dict[str, Any] = {}
        for block in blocks:
            if isinstance(block, N.Command) and block.name == "set" and block.args is not None:
                unknown = [key for key in block.args.keywords if key not in STRUCTURE_KEYS]
                for key in unknown:
                    self.report(core_error("P3115", block.args.span, key=key))
                overrides = merge_overrides(overrides, {k: v for k, v in block.args.keywords.items()
                                                       if k in STRUCTURE_KEYS})
                continue
            if overrides:
                inner = getattr(block, "set_overrides", None)
                block.set_overrides = merge_overrides(overrides, inner) if inner else dict(overrides)
            result.append(block)
        return result

    def _allowed_in(self, container: str, block: Any) -> bool:
        """Blocks inserted into a table or row (decision 37)."""
        if isinstance(block, N.BlankLine):
            return True
        if container == "table" and (isinstance(block, N.TableRow) or
                                     isinstance(block, N.Command) and block.name in ("row", "caption")):
            return True
        if container == "row" and isinstance(block, N.Command) and block.name == "cell":
            return True
        label = "|" + block.name if isinstance(block, N.Command) else type(block).__name__.lower()
        self.report(core_error("P1226", block.span, what=label, container=container))
        return False

    def _resolve_command(self, name: str, ctx: _Ctx, span: Span) -> Any:
        """The value named by a command (``sign``, ``business.sign``)."""
        parts = [nfkc(part) for part in name.split(".")]  # names compare by NFKC (3.9)
        try:
            value = ctx.env.lookup(parts[0], span)
        except CoreError as exc:
            if exc.diagnostic.code == "P2201":
                diagnostic = error("P2601", span, name=name)
                glued = self._glued_prefix(parts[0], ctx)
                if glued is not None:
                    # "|sellerом": the text after the name is glued to it (3.2).
                    diagnostic.hint("help.glued_name", name=glued)
                raise CoreError(diagnostic) from None
            raise
        from primula.core.builtins import get_attribute

        for part in parts[1:]:
            value = get_attribute(self.interp, value, part, span)
        return value

    @staticmethod
    def _glued_prefix(name: str, ctx: _Ctx) -> str | None:
        """The longest proper prefix of ``name`` that is a known command or name (3.2)."""
        for end in range(len(name) - 1, 0, -1):
            prefix = name[:end]
            if prefix in BUILTIN_COMMANDS:
                return prefix
            try:
                ctx.env.lookup(prefix, None)
            except CoreError:
                continue
            return prefix
        return None

    def _call_command(self, node: Any, ctx: _Ctx, out: list[Any], *, block_form: bool) -> None:
        """Call a macro or function used as a command (3.2, decision 48)."""
        span = node.name_span if hasattr(node, "name_span") else node.span
        args = node.args
        positional, named = ([], {}) if args is None else self.interp.eval_arguments(
            args.call.args, [kw for kw in args.call.keywords if kw.arg != "when"], ctx.env, args.fragment)
        if node.name == "call":
            if not positional:
                raise core_error("P2632", node.span)
            function, positional = positional[0], positional[1:]
        else:
            function = self._resolve_command(node.name, ctx, span)
        body: Content | None = None
        if isinstance(node, N.Command):
            if node.form == "env":
                body = content_blocks(self._expand_blocks(node.children, ctx))
            elif node.form == "line":
                body = content_inline(self._expand_inlines(node.body, ctx, node.span))
        elif node.body is not None:
            body = content_inline(self._expand_inlines(node.body, ctx, node.span))
        if isinstance(function, Macro):
            result: Any = self.call_macro(function, positional, named, node.span, body)
        elif isinstance(function, (Function, Builtin, BoundMethod)):
            if body is not None:
                named = {**named, "body": body}
            result = self.interp.call(function, positional, named, node.span)
        else:
            raise CoreError(error("P2602", span, name=node.name, type=type_name(function)).hint("help.insert_value"))
        if block_form:
            if isinstance(result, Content) and result.kind == "blocks":
                out.extend(result.nodes)
            else:
                inlines = self._value_inlines(result, node.span)
                if inlines:
                    out.append(N.Paragraph(node.span, inlines))
        else:
            out.extend(self._content_inline(result, node.span, node.name))

    # --- inline ----------------------------------------------------------

    def _expand_inlines(self, inlines: list[Any], ctx: _Ctx, span: Span) -> list[Any]:
        out: list[Any] = []
        for node in inlines:
            try:
                self._expand_inline(node, ctx, out)
            except CoreError as exc:
                self.report(exc)
        return _merge_text(out)

    def _expand_inline(self, node: Any, ctx: _Ctx, out: list[Any]) -> None:
        if isinstance(node, (N.Text, N.LineBreak)):
            out.append(node)
        elif isinstance(node, N.Comment):
            return
        elif isinstance(node, N.Expr):
            if node.expr is not None:
                value = self.interp.eval(node.expr.node, ctx.env, node.expr.fragment)
                out.extend(self._content_inline(value, node.span, None))
        elif isinstance(node, N.Formula):
            new = replace(node)
            new.env = ctx.env  # type: ignore[attr-defined]
            out.append(new)
        elif isinstance(node, N.InlineIf) and self.options.review:
            # --review: every branch, coloured, with the condition in a Writer comment (9.2).
            taken_found = False
            for index, branch in enumerate(node.branches):
                truth = False
                if not taken_found and (branch.cond is None or self.interp.truthy(
                        self.interp.eval(branch.cond.node, ctx.env, branch.cond.fragment))):
                    truth = taken_found = True
                body = self._expand_inlines(branch.body, ctx, branch.span)
                if index:
                    out.append(N.Text(branch.span, " "))  # branches side by side need a gap
                style = N.StyleRef(branch.span, "ReviewTrue" if truth else "ReviewFalse")
                out.append(N.StyleSpan(branch.span, style, None, body))
                note = N.Text(branch.span, _branch_label(node.branches, index))
                out.append(N.InlineCommand(branch.span, "review_note", branch.span, None, [note]))
        elif isinstance(node, N.InlineIf):
            taken = None
            for branch in node.branches:
                if branch.cond is None or self.interp.truthy(
                        self.interp.eval(branch.cond.node, ctx.env, branch.cond.fragment)):
                    taken = branch
                    out.extend(self._expand_inlines(branch.body, ctx, branch.span))
                    break
            self._skipped_branches(node.branches, taken)
        elif isinstance(node, N.InlineFor):
            iterable = self.interp.eval(node.loop.node.iter, ctx.env, node.loop.fragment)
            for item in self.interp.iterate(iterable, node.loop.span):
                env = Env(ctx.env.globals, ctx.env, None)
                self.interp.assign(node.loop.node.target, item, env, node.loop.fragment)
                out.extend(self._expand_inlines(node.body, replace(ctx, env=env, local=True), node.span))
        elif isinstance(node, N.InlineCommand):
            self._expand_inline_command(node, ctx, out)
        elif isinstance(node, N.Short):
            body = self._expand_inlines(node.body, ctx, node.span)
            if node.mark == "?":
                if self.registry.settings.get("placeholders") == "final":
                    # placeholders("final") (decision 123): a filled document — plain text, no warning.
                    out.extend(body)
                    return
                # Every placeholder left in the document is a warning (4.2);
                # --strict turns it into an error.
                text = "".join(n.value for n in body if isinstance(n, N.Text)).strip()
                self.sink.emit(warning("P2635", node.span, text=text))
            out.append(replace(node, args=self._eargs(node.args, ctx), body=body))
        elif isinstance(node, N.StyleSpan):
            out.append(replace(node, style=self._style_ref(node.style, ctx), args=self._eargs(node.args, ctx),
                               body=self._expand_inlines(node.body, ctx, node.span)))
        elif isinstance(node, N.Reference):
            out.append(replace(node, args=self._eargs(node.args, ctx)))
        else:  # pragma: no cover - all inline kinds are handled
            out.append(node)

    def _expand_inline_command(self, node: N.InlineCommand, ctx: _Ctx, out: list[Any]) -> None:
        name = node.name
        if name in ("let", "export", "import"):
            if ctx.local and name == "let":
                self._local_let(node.args, ctx)
            return
        if name == "call" or not _is_builtin(name):
            self._call_command(node, ctx, out, block_form=False)
            return
        if name == "track":
            raise CoreError(error("P5302", node.name_span, command=name, where=Key("parallel.outside_segment"))
                            .hint("help.parallel"))
        new = replace(node, args=self._eargs(node.args, ctx))
        if name == "img":
            self._image_path(new, ctx)
        if name == "link":
            self._check_link(new)
        if node.body is not None:
            if name == "cell" and ctx.container == "cell":
                new.body = self._cell_inlines(node.body, ctx, node.span, new)
            else:
                new.body = self._expand_inlines(node.body, ctx, node.span)
        out.append(new)

    @staticmethod
    def _check_link(node: Any) -> None:
        """``|link("url"){текст}`` (4.2, decision 120): one string — the address."""
        args = node.args
        if args is None or len(args.positional) != 1 or not isinstance(args.positional[0], str) \
                or not args.positional[0] or args.keywords:
            raise core_error("P2609", args.span if args is not None else node.span, command="link",
                             problem="one URL string is required")

    def _style_ref(self, style: N.StyleRef, ctx: _Ctx) -> N.StyleRef:
        """Evaluate a computed style reference ``|.(expr)`` (4.3)."""
        if style.expr is None:
            return style
        value = self.interp.eval(style.expr.node, ctx.env, style.expr.fragment)
        if isinstance(value, str):
            return N.StyleRef(style.span, value)
        raise core_error("P2633", style.span, type=type_name(value))

    # --- values in text (decision 47) ----------------------------------

    def _content_inline(self, value: Any, span: Span, name: str | None) -> list[Any]:
        """Inline nodes for a value inserted inside a line."""
        if isinstance(value, Content):
            if value.kind == "inline":
                return list(value.nodes)
            blocks = [b for b in value.nodes if not isinstance(b, N.BlankLine)]
            if not blocks:
                return []
            if len(blocks) == 1 and isinstance(blocks[0], N.Paragraph):
                return list(blocks[0].body)
            raise core_error("P2605", span, name=name or "")
        return self._value_inlines(value, span)

    def _value_inlines(self, value: Any, span: Span) -> list[Any]:
        """Text of a value by the ``str()`` rules (decision 47)."""
        if isinstance(value, str):
            return [N.Text(span, value)] if value else []
        if isinstance(value, Content):
            return self._content_inline(value, span, None)
        if isinstance(value, int) and not isinstance(value, bool):
            # An integer value (scale 0) needs no decimal separator: no warning.
            return [N.Text(span, to_str(value))]
        if isinstance(value, (float, DateTime, Length)) or type(value).__name__ == "Decimal":
            self.sink.emit(warning("P2604", span, type=type_name(value)).hint("help.format_value"))
            return [N.Text(span, to_str(value))]
        raise CoreError(error("P2603", span, type=type_name(value)).hint("help.text_value"))


def _tag_inclusion(nodes: list[Any], state: FileState) -> None:
    """Record the inclusion on ID holders and references (decision 74).

    ``id_scopes`` lists ``(namespace, include span, fragment path)`` from
    the outermost inclusion to the innermost; the structure phase builds
    the ``ns.`` prefix of IDs from it and reports a fragment with IDs
    included twice without ``ns=``.
    """
    entry = (state.namespace, state.frame[1] if state.frame else None, state.loaded.path)
    for node in iter_tree(nodes):
        args = getattr(node, "args", None)
        if isinstance(node, N.Reference) or (isinstance(args, EArgs) and "id" in args.keywords):
            node.id_scopes = [entry, *getattr(node, "id_scopes", [])]


def _tag_track(nodes: list[Any], track_id: str, block: N.Command, primary: str | None) -> None:
    """IDs inside a track block get the prefix of the track: ``uk.services`` (7.7).

    The track is recorded as an outer inclusion with the namespace of the
    track id (decision 74 mechanism): the structure phase builds the full ID
    from it, and a reference inside the track first looks for an ID of its
    own track.  The "path" is unique per track block, so a repeated ID is
    the ordinary duplicate P4102.  A reference in a non-primary track also
    looks in the ``primary`` track before the IDs outside the tracks.
    """
    entry = (track_id, block.span, f"<track {id(block)}>")
    for node in iter_tree(nodes):
        args = getattr(node, "args", None)
        if isinstance(node, N.Reference) or (isinstance(args, EArgs) and "id" in args.keywords):
            node.id_scopes = [entry, *getattr(node, "id_scopes", [])]
        if isinstance(node, N.Reference) and primary is not None:
            node.track_primary = primary


def _is_value_name(name: str, env: Env) -> bool:
    """A name of a parameter or variable, not a function, macro or the records of a track (7.7)."""
    if name in ("track", "segment"):
        return False
    try:
        value = env.lookup(name, None)
    except CoreError:
        return True  # a name bound inside the expression (comprehension)
    return not isinstance(value, (Builtin, Function, BoundMethod, Macro, ModuleValue))


def _block_label(block: Any) -> str:
    """A block for messages: ``|name`` of a command, otherwise the kind of the block."""
    if isinstance(block, N.Command):
        return "|" + block.name
    return type(block).__name__.lower()


def _part_scope_name(name: str) -> bool:
    """A part scope: an identifier with ``-`` and ``.`` like an ID (5.6), without ``:``."""
    return bool(name) and ":" not in name and is_identifier(name.replace("-", "_").replace(".", "_"))


def _merge_text(nodes: list[Any]) -> list[Any]:
    """Merge adjacent text nodes of one source (expression values, literals)."""
    merged: list[Any] = []
    for node in nodes:
        previous = merged[-1] if merged else None
        if isinstance(node, N.Text) and isinstance(previous, N.Text) \
                and previous.span.source is node.span.source and previous.span.start <= node.span.start:
            merged[-1] = N.Text(Span(node.span.source, previous.span.start, max(previous.span.end, node.span.end)),
                                previous.value + node.value)
        elif isinstance(node, N.Text) and not node.value:
            continue
        else:
            merged.append(node)
    return merged


def _is_builtin(name: str) -> bool:
    """Built-in command names (appendix 2.1) are passed to later stages."""
    return name in BUILTIN_COMMANDS or name.startswith("field.")


def _inline_lists(block: Any) -> list[list[Any]]:
    """Inline content lists of a block (for collecting inline ``|let``)."""
    lists = []
    if isinstance(block, (N.Paragraph, N.Heading, N.Clause, N.Admonition, N.StyleBlock, N.ListItem, N.Command)):
        if block.body:
            lists.append(block.body)
    if isinstance(block, N.TableRow):
        lists.extend(cell.body for cell in block.cells)
    return lists


def _walk_blocks(blocks: list[Any]) -> Any:
    for block in blocks:
        yield block
        for attribute in ("children",):
            children = getattr(block, attribute, None)
            if children:
                yield from _walk_blocks(children)
        if isinstance(block, N.IfBlock):
            for branch in block.branches:
                yield from _walk_blocks(branch.children)


def _branch_label(branches: list[Any], index: int) -> str:
    """«if: cond», «elif: cond», «else» — the label of a branch in the ``--review`` mode."""
    branch = branches[index]
    if branch.cond is None:
        return "else"
    keyword = "if" if index == 0 else "elif"
    return f"{keyword}: {branch.cond.fragment.segment(branch.cond.node)}"


def _markup_only(branches: list[Any]) -> bool:
    """Branches without definitions (``|let``, ``|code:``, macros, imports): ``--review`` may show all."""
    for branch in branches:
        for node in iter_tree(getattr(branch, "children", None) or []):
            if isinstance(node, (N.CodeBlock, N.DefBlock)) or (
                    isinstance(node, (N.Command, N.InlineCommand)) and node.name in ("let", "export", "import")):
                return False
    return True


def _exported(scope: GlobalScope, name: str, span: Any) -> Any:
    """The value of ``name`` exported by ``|export("name")``: P2637 when the fragment does not define it."""
    if name not in scope.definitions:
        raise core_error("P2637", span, name=name)
    return scope.lookup(name, None)
