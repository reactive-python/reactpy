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


def inspect_event_handler(func: Callable) -> tuple[bool, bool, int | None]:
    """Detect ``preventDefault``/``stopPropagation``/``debounce`` usage.

    Walks the bytecode of ``func`` looking for the patterns:

    - ``event.preventDefault()`` -> ``prevent_default = True``
    - ``event.stopPropagation()`` -> ``stop_propagation = True``
    - ``event.debounce = <int>``  -> ``debounce = <int>``

    The ``debounce`` value can come from any of the following:

    - An integer literal (``LOAD_CONST`` / ``LOAD_SMALL_INT``)
    - A function argument with a numeric default
    - A closure variable whose captured value is numeric
    - An integer constant in ``code.co_consts`` (best-effort, covers
      certain compile-time-folded module-level names)

    Module-level globals looked up via ``LOAD_GLOBAL``/``LOAD_NAME`` cannot
    be resolved from the function alone, so users must pass
    ``debounce=...`` explicitly in that case.

    Returns ``(prevent_default, stop_propagation, debounce)``.
    """
    code = func.__code__

    prevent_default = False
    stop_propagation = False
    debounce: int | None = None

    if code.co_argcount <= 0:
        return prevent_default, stop_propagation, debounce

    names = code.co_names
    check_prevent_default = "preventDefault" in names
    check_stop_propagation = "stopPropagation" in names
    check_debounce = "debounce" in names

    if not (check_prevent_default or check_stop_propagation or check_debounce):
        return prevent_default, stop_propagation, debounce

    event_arg_name = code.co_varnames[0]
    instructions = list(dis.get_instructions(code))
    arg_defaults = _function_arg_defaults(func)
    closure_by_name = _closure_lookup(func)
    constant_ints_by_name = _constant_ints_by_name(code)

    last_was_event = False
    # When the function assigns ``event.debounce`` in multiple branches we
    # cannot know which one runs at runtime. If any assignment uses an
    # unresolvable value (e.g. a local variable) we treat the whole detection
    # as ambiguous and return ``None`` rather than picking a fallback literal.
    debounce_tainted = False

    for index, instr in enumerate(instructions):
        if (
            instr.opname in ("LOAD_FAST", "LOAD_FAST_BORROW")
            and instr.argval == event_arg_name
        ):
            last_was_event = True
            continue

        # CPython 3.11+ may fuse ``LOAD_FAST value; LOAD_FAST target`` into
        # the superinstruction ``LOAD_FAST_BORROW_LOAD_FAST_BORROW`` whose
        # argval is ``(value_name, target_name)``. Treat it like a normal
        # event load when the target matches.
        if (
            instr.opname == "LOAD_FAST_BORROW_LOAD_FAST_BORROW"
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
            check_debounce
            and instr.opname == "STORE_ATTR"
            and instr.argval == "debounce"
        ):
            candidate = _resolve_debounce_value(
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

        if not (check_prevent_default or check_stop_propagation or check_debounce):
            break

        last_was_event = False

    return prevent_default, stop_propagation, debounce


def _function_arg_defaults(func: Callable) -> dict[str, int]:
    """Return ``{arg_name: default}`` for numeric defaults of ``func``.

    Includes positional defaults (``__defaults__``) and keyword-only defaults
    (``__kwdefaults__``).
    """
    code = func.__code__
    result: dict[str, int] = {}

    positional_defaults = getattr(func, "__defaults__", None)
    if positional_defaults:
        argcount = code.co_argcount
        n_defaults = len(positional_defaults)
        first_default_idx = argcount - n_defaults
        for offset, value in enumerate(positional_defaults):
            if not (isinstance(value, int) and not isinstance(value, bool)):
                continue
            name = code.co_varnames[first_default_idx + offset]
            result[name] = value

    kwdefaults = getattr(func, "__kwdefaults__", None) or {}
    for name, value in kwdefaults.items():
        if isinstance(value, int) and not isinstance(value, bool):
            result[name] = value

    return result


def _closure_lookup(func: Callable) -> dict[str, int]:
    """Return ``{name: captured_value}`` for numeric closure variables on ``func``."""
    closure = getattr(func, "__closure__", None)
    if not closure:
        return {}
    freevars = getattr(func.__code__, "co_freevars", ())
    result: dict[str, int] = {}
    for idx, cell in enumerate(closure):
        if idx >= len(freevars):
            break
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if isinstance(value, int) and not isinstance(value, bool):
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


def _resolve_debounce_value(
    instructions: list[dis.Instruction],
    store_index: int,
    event_arg_name: str,
    arg_defaults: dict[str, int],
    closure_by_name: dict[str, int],
    constant_ints_by_name: dict[str, int],
) -> Any:
    """Inspect the bytecode immediately before ``STORE_ATTR debounce`` to find
    the value being stored. Returns the resolved value, ``None`` when the
    value cannot be determined.
    """
    if store_index < 1:
        return None

    prev = instructions[store_index - 1]

    # CPython 3.11+ superinstruction: argval is ``(value_name, target_name)``.
    # The value comes from a function argument default.
    if prev.opname == "LOAD_FAST_BORROW_LOAD_FAST_BORROW":
        names = prev.argval
        if isinstance(names, Iterable) and not isinstance(names, str):
            names = list(names)
            if len(names) == _LOAD_FAST_BORROW_PAIR_SIZE and names[1] == event_arg_name:
                return arg_defaults.get(names[0])
        return None

    # Otherwise the value is loaded by the instruction two slots back, with
    # the event target loaded immediately before STORE_ATTR.
    if store_index < _STORE_ATTR_VALUE_OFFSET:
        return None

    val_instr = instructions[store_index - 2]
    target_instr = prev

    if target_instr.opname not in ("LOAD_FAST", "LOAD_FAST_BORROW"):
        return None
    if target_instr.argval != event_arg_name:
        return None

    if val_instr.opname in ("LOAD_CONST", "LOAD_SMALL_INT"):
        value = val_instr.argval
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return None

    if val_instr.opname in ("LOAD_FAST", "LOAD_FAST_BORROW"):
        return arg_defaults.get(val_instr.argval)

    if val_instr.opname == "LOAD_DEREF":
        return closure_by_name.get(val_instr.argval)

    return None
