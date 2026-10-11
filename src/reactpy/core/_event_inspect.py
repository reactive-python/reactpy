"""
In order to retain a JavaScript-like event handler API, ReactPy allows users to configure event handlers with `event.debounce = <milliseconds>` or `event.eventProxy = <bool>`.
Implementing this syntax necessitates inspecting the bytecode of event handler functions.
"""

from __future__ import annotations

import dis
from collections.abc import Callable, Iterable
from types import CodeType
from typing import Any

# Number of operands packed into a ``LOAD_FAST_BORROW_LOAD_FAST_BORROW``
# superinstruction (value name + target name).
_LOAD_FAST_BORROW_PAIR_SIZE = 2

# Number of slots back from ``STORE_ATTR`` where the value expression lives
# for the standard ``target = value; obj.attr = target`` shape.
_STORE_ATTR_VALUE_OFFSET = 2


def _is_plain_int(value: Any) -> bool:
    """Whether ``value`` is an ``int`` which is not a ``bool``"""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_bool(value: Any) -> bool:
    """Whether ``value`` is a ``bool`` rather than a number dressed up as one"""
    return isinstance(value, bool)


def _handler_code(func: Callable) -> CodeType | None:
    """The bytecode of the callable a user handed us

    A handler is normally a function, but an object whose ``__call__`` is a coroutine
    is a handler too, and its bytecode lives on the class.
    """
    code = getattr(func, "__code__", None)
    if code is not None:
        return code
    # a callable object's own ``__call__`` is defined on its class
    try:
        call = type(func).__call__
    except AttributeError:  # nocov - only a metaclass can hide this
        return None
    return getattr(call, "__code__", None)


def _event_arg_name(func: Callable, code: CodeType | None) -> str | None:
    """What the given handler calls the event it is handed, if it takes one"""
    if code is None:
        return None
    # the first parameter of a callable object's ``__call__`` is the object itself
    offset = 0 if hasattr(func, "__code__") else 1
    if code.co_argcount <= offset:
        return None
    return code.co_varnames[offset]


def inspect_event_handler(
    func: Callable,
) -> tuple[bool, bool | str, int | None, bool | None]:
    """Detect ``preventDefault``/``stopPropagation``/``debounce``/``eventProxy`` usage.

    Walks the bytecode of ``func`` looking for the patterns:

    - ``event.preventDefault()`` -> ``prevent_default = True``
    - ``event.stopPropagation()`` -> ``stop_propagation = True``
    - ``event.stopImmediatePropagation()`` -> ``stop_propagation = "immediate"``
    - ``event.debounce = <int>``  -> ``debounce = <int>``
    - ``event.eventProxy = <bool>`` -> ``event_proxy = <bool>``

    The value behind ``debounce`` and ``eventProxy`` can come from any of the
    following:

    - A literal (``LOAD_CONST`` / ``LOAD_SMALL_INT``)
    - A function argument with a matching default
    - A closure variable whose captured value matches
    - An integer constant in ``code.co_consts`` (best-effort, covers
      certain compile-time-folded module-level names)

    Module-level globals looked up via ``LOAD_GLOBAL``/``LOAD_NAME`` cannot
    be resolved from the function alone, so users must pass
    ``debounce=...``/``event_proxy=...`` explicitly in that case.

    Returns ``(prevent_default, stop_propagation, debounce, event_proxy)``, where
    ``stop_propagation`` is the string ``"immediate"`` if the handler asked to stop
    *other listeners* as well, and ``event_proxy`` is :data:`None` for a handler
    which never said anything about reading past the event it was handed.
    """
    prevent_default = False
    stop_propagation = False
    stop_immediate_propagation = False
    debounce: int | None = None
    event_proxy: bool | None = None

    code = _handler_code(func)
    event_arg_name = _event_arg_name(func, code)
    if code is None or event_arg_name is None:
        # Nothing to walk, or nothing to walk from
        return prevent_default, stop_propagation, debounce, event_proxy

    names = code.co_names
    check_prevent_default = "preventDefault" in names
    check_stop_propagation = "stopPropagation" in names
    check_stop_immediate_propagation = "stopImmediatePropagation" in names
    check_debounce = "debounce" in names
    check_event_proxy = "eventProxy" in names

    if not (
        check_prevent_default
        or check_stop_propagation
        or check_stop_immediate_propagation
        or check_debounce
        or check_event_proxy
    ):
        return prevent_default, stop_propagation, debounce, event_proxy

    instructions = list(dis.get_instructions(code))
    arg_defaults = _function_arg_defaults(func)
    closure_by_name = _closure_lookup(func)
    constant_ints_by_name = _constant_ints_by_name(code)
    # The same lookups again, keeping only the ``bool`` values ``eventProxy`` accepts
    arg_flags = _function_arg_defaults(func, _is_bool)
    closure_flags = _closure_lookup(func, _is_bool)

    last_was_event = False
    # When the function assigns ``event.debounce`` in multiple branches we
    # cannot know which one runs at runtime. If any assignment uses an
    # unresolvable value (e.g. a local variable) we treat the whole detection
    # as ambiguous and return ``None`` rather than picking a fallback literal.
    debounce_tainted = False
    event_proxy_tainted = False

    for index, instr in enumerate(instructions):
        if (
            instr.opname in ("LOAD_FAST", "LOAD_FAST_BORROW")
            and instr.argval == event_arg_name
        ):
            last_was_event = True
            continue

        # CPython 3.11+ may fuse ``LOAD_FAST value; LOAD_FAST target`` into
        # a superinstruction whose argval is ``(value_name, target_name)``.
        # Two variants may appear depending on the interpreter:
        #   * ``LOAD_FAST_LOAD_FAST`` (CPython 3.13+)
        #   * ``LOAD_FAST_BORROW_LOAD_FAST_BORROW`` (CPython 3.14+)
        # Treat either as a normal event load when the target matches.
        if (
            instr.opname in ("LOAD_FAST_LOAD_FAST", "LOAD_FAST_BORROW_LOAD_FAST_BORROW")
            and isinstance(instr.argval, (list, tuple))
            and len(instr.argval) == _LOAD_FAST_BORROW_PAIR_SIZE
            and instr.argval[1] == event_arg_name
        ):
            last_was_event = True
            continue

        if not last_was_event:
            continue

        if instr.opname in ("LOAD_METHOD", "LOAD_ATTR"):
            if check_prevent_default and instr.argval == "preventDefault":
                prevent_default = True
                check_prevent_default = False
            elif check_stop_propagation and instr.argval == "stopPropagation":
                stop_propagation = True
                check_stop_propagation = False
            elif (
                check_stop_immediate_propagation
                and instr.argval == "stopImmediatePropagation"
            ):
                stop_immediate_propagation = True
                stop_propagation = True
                check_stop_immediate_propagation = False
        elif (
            check_debounce
            and instr.opname == "STORE_ATTR"
            and instr.argval == "debounce"
        ):
            candidate = _resolve_stored_value(
                instructions,
                index,
                event_arg_name,
                arg_defaults,
                closure_by_name,
                constant_ints_by_name,
            )
            if isinstance(candidate, int) and not isinstance(candidate, bool):
                if not debounce_tainted:
                    debounce = candidate
                    check_debounce = False
            elif candidate is None:
                # Value source is a name we cannot resolve at this point.
                # This could be a module-level global, a local variable, or
                # an expression. We can't determine the real debounce, so we
                # refuse to guess even if a later literal assignment exists.
                debounce_tainted = True
                debounce = None
                check_debounce = False
        elif (
            check_event_proxy
            and instr.opname == "STORE_ATTR"
            and instr.argval == "eventProxy"
        ):
            candidate = _resolve_stored_value(
                instructions,
                index,
                event_arg_name,
                arg_flags,
                closure_flags,
                {},
                is_value=_is_bool,
            )
            if isinstance(candidate, bool):
                if not event_proxy_tainted:
                    event_proxy = candidate
                    check_event_proxy = False
            elif candidate is None:
                # Same as ``debounce`` above: a value we cannot settle from the
                # bytecode alone leaves the handler without an opinion, rather
                # than a guessed one.
                event_proxy_tainted = True
                event_proxy = None
                check_event_proxy = False

        if not (
            check_prevent_default
            or check_stop_propagation
            or check_stop_immediate_propagation
            or check_debounce
            or check_event_proxy
        ):
            break

        last_was_event = False

    return (
        prevent_default,
        "immediate" if stop_immediate_propagation else stop_propagation,
        debounce,
        event_proxy,
    )


def _function_arg_defaults(
    func: Callable,
    is_value: Callable[[Any], bool] = _is_plain_int,
) -> dict[str, Any]:
    """Return ``{arg_name: default}`` for the defaults of ``func`` which ``is_value``
    accepts - plain integers unless another shape is asked for.

    Includes positional defaults (``__defaults__``) and keyword-only defaults
    (``__kwdefaults__``).
    """
    code = _handler_code(func)
    result: dict[str, Any] = {}
    if code is None:
        return result

    positional_defaults = getattr(func, "__defaults__", None)
    if positional_defaults:
        argcount = code.co_argcount
        n_defaults = len(positional_defaults)
        first_default_idx = argcount - n_defaults
        for offset, value in enumerate(positional_defaults):
            if not is_value(value):
                continue
            name = code.co_varnames[first_default_idx + offset]
            result[name] = value

    kwdefaults = getattr(func, "__kwdefaults__", None) or {}
    for name, value in kwdefaults.items():
        if is_value(value):
            result[name] = value

    return result


def _closure_lookup(
    func: Callable,
    is_value: Callable[[Any], bool] = _is_plain_int,
) -> dict[str, Any]:
    """Return ``{name: captured_value}`` for the closure variables of ``func`` which
    ``is_value`` accepts - plain integers unless another shape is asked for.
    """
    closure = getattr(func, "__closure__", None)
    if not closure:
        return {}
    code = _handler_code(func)
    freevars = getattr(code, "co_freevars", ()) if code is not None else ()
    result: dict[str, Any] = {}
    for idx, cell in enumerate(closure):
        if idx >= len(freevars):
            break
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if is_value(value):
            result[freevars[idx]] = value
    return result


def _constant_ints_by_name(code: CodeType) -> dict[str, int]:
    """Return names whose values are integer constants.

    CPython stores per-name constants alongside ``code.co_names`` for certain
    bytecode shapes (e.g. ``LOAD_FAST`` of a module-level constant that the
    compiler inlined into the function's ``co_consts``). We don't have a
    positional mapping for that, so this returns an empty mapping by default.
    It exists as an extension point.
    """
    return {}


def _resolve_stored_value(
    instructions: list[dis.Instruction],
    store_index: int,
    event_arg_name: str,
    values_by_name: dict[str, Any],
    closure_by_name: dict[str, Any],
    constant_ints_by_name: dict[str, Any],
    is_value: Callable[[Any], bool] = _is_plain_int,
) -> Any:
    """Inspect the bytecode immediately before ``STORE_ATTR`` to find the value being
    stored on the event, where ``values_by_name`` and ``closure_by_name`` hold the
    names whose values ``is_value`` accepts. Returns the resolved value, ``None`` when
    the value cannot be determined.
    """
    if store_index < 1:
        return None

    prev = instructions[store_index - 1]

    # CPython 3.11+ superinstruction: argval is ``(value_name, target_name)``.
    # The value comes from a function argument default. Two superinstructions
    # may appear here depending on the interpreter version:
    #   * ``LOAD_FAST_LOAD_FAST`` (CPython 3.13+)
    #   * ``LOAD_FAST_BORROW_LOAD_FAST_BORROW`` (CPython 3.14+)
    if prev.opname in ("LOAD_FAST_LOAD_FAST", "LOAD_FAST_BORROW_LOAD_FAST_BORROW"):
        names = prev.argval
        if isinstance(names, Iterable) and not isinstance(names, str):
            names = list(names)
            if len(names) == _LOAD_FAST_BORROW_PAIR_SIZE and names[1] == event_arg_name:
                return values_by_name.get(names[0])
        return None

    # Otherwise the value is loaded by the instruction two slots back, with
    # the event target loaded immediately before STORE_ATTR.
    if store_index < _STORE_ATTR_VALUE_OFFSET:
        return None

    val_instr = instructions[store_index - 2]
    target_instr = prev

    if target_instr.opname not in (
        "LOAD_FAST",
        "LOAD_FAST_BORROW",
        # CPython 3.13+ may fuse two ``LOAD_FAST`` instructions into
        # ``LOAD_FAST_LOAD_FAST`` whose argval is ``(value_name, target_name)``.
        # The detector above already covers this case whenever the value comes
        # from a default, but the standalone form can also appear if the value
        # isn't a default and the event is loaded separately.
        "LOAD_FAST_LOAD_FAST",
    ):
        return None
    if target_instr.argval != event_arg_name:
        return None

    if val_instr.opname in ("LOAD_CONST", "LOAD_SMALL_INT"):
        value = val_instr.argval
        if is_value(value):
            return value
        return None

    if val_instr.opname in ("LOAD_FAST", "LOAD_FAST_BORROW"):
        return values_by_name.get(val_instr.argval)

    if val_instr.opname == "LOAD_DEREF":
        return closure_by_name.get(val_instr.argval)

    return None
