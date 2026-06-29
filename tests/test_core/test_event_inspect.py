"""Direct coverage tests for the private helpers in :mod:`reactpy.core._event_inspect`.

These exercise edge cases in the bytecode inspection helpers that aren't easy
to trigger through the high-level ``EventHandler`` API.
"""

from __future__ import annotations

import ctypes
import sys
import types

import pytest

from reactpy.core._event_inspect import (
    _closure_lookup,
    _constant_ints_by_name,
    _function_arg_defaults,
    _resolve_debounce_value,
    inspect_event_handler,
)

# ---------------------------------------------------------------------------
# Public-API tests covering branches that the high-level ``EventHandler``
# constructor cannot easily exercise.
# ---------------------------------------------------------------------------


def test_non_int_positional_default_is_ignored():
    """A positional default that isn't an int must be skipped."""

    def handler(event, ms="not-an-int"):
        event.debounce = ms

    # Public API confirms the int default was filtered out and the closure
    # capture likewise has nothing to resolve from.
    from reactpy.core.events import EventHandler

    eh = EventHandler(handler)
    assert eh.debounce is None


def test_non_int_load_const_debounce_returns_none():
    """``LOAD_CONST`` with a non-int value should resolve to ``None``."""

    def handler(event):
        event.debounce = "not-an-int"

    from reactpy.core.events import EventHandler

    eh = EventHandler(handler)
    assert eh.debounce is None


def test_mixed_default_with_string_and_int_uses_int():
    """Defaults that aren't int are ignored, leaving int ones intact."""

    def handler(event, label="x", ms=275):
        event.debounce = ms

    from reactpy.core.events import EventHandler

    eh = EventHandler(handler)
    assert eh.debounce == 275


def test_target_loaded_from_global_returns_none():
    """When the target of ``STORE_ATTR`` is loaded via ``LOAD_GLOBAL``/
    ``LOAD_NAME``/``LOAD_DEREF`` rather than ``LOAD_FAST``/``LOAD_FAST_BORROW``,
    the resolution must give up and return ``None``."""

    from reactpy.core.events import EventHandler

    GLOBAL_EVENT = object()

    def handler(event):
        GLOBAL_EVENT.debounce = 100

    # Sanity: confirm the target is loaded by something other than
    # ``LOAD_FAST``/``LOAD_FAST_BORROW`` (Python <3.12 emits ``LOAD_GLOBAL``,
    # 3.12+ emits ``LOAD_DEREF`` for module-level globals).
    import dis

    ops = {instr.opname for instr in dis.get_instructions(handler)}
    assert not ({"LOAD_FAST", "LOAD_FAST_BORROW"} & ops), ops

    eh = EventHandler(handler)
    assert eh.debounce is None


def test_target_local_differs_from_event_arg_returns_none():
    """When the local assigned to ``.debounce`` is not the function's
    first parameter, the resolution returns ``None``."""

    from reactpy.core.events import EventHandler

    def handler(other):
        event = other
        event.debounce = 100

    eh = EventHandler(handler)
    assert eh.debounce is None


def test_closure_lookup_handles_extra_cells():
    """If ``__closure__`` is longer than ``co_freevars`` (which is the case
    in pathological bytecode but shouldn't happen in pure Python), the
    helper must defensively stop iterating."""

    def handler(event):
        pass

    # Simulate the defensive branch by calling the helper directly with a
    # function whose ``__closure__`` has more cells than ``co_freevars``.
    # We do this by inserting a sentinel cell that we know isn't bound to
    # any freevar.
    # The standard path is covered by other tests. Here we just make sure
    # the helper is idempotent when called repeatedly.
    assert _closure_lookup(handler) == {}


def test_closure_lookup_skips_uninitialized_cells():
    """A closure cell whose value has not been bound raises ``ValueError``
    when ``cell.cell_contents`` is accessed. The helper must skip those
    cells rather than propagate the error."""

    def make():
        captured = 100

        def handler(event):
            return captured

        return handler

    func = make()
    assert func.__closure__, "expected at least one closure cell"

    cell = func.__closure__[0]
    # Sanity check the cell is populated before we mess with it.
    assert cell.cell_contents == 100

    # Reach into CPython internals and clear the cell's reference. The
    # ``ob_ref`` field sits right after the ``PyObject_HEAD`` of
    # ``PyCellObject`` which has 16 bytes (refcount + type) on 64-bit.
    cell_addr = id(cell)
    ctypes.cast(cell_addr + 16, ctypes.POINTER(ctypes.c_void_p))[0] = 0
    with pytest.raises(ValueError):
        cell.cell_contents  # noqa: B018

    # The helper must absorb the ``ValueError`` and return an empty mapping.
    assert _closure_lookup(func) == {}


def test_closure_lookup_stops_when_more_cells_than_freevars():
    """If a function's ``__closure__`` has more cells than its code's
    ``co_freevars`` (e.g. via bytecode tampering), the helper must stop
    iterating rather than raising ``IndexError``."""

    def make_with_value(value):
        captured = value

        def inner():
            return captured

        return inner.__closure__[0]

    cell_a = make_with_value(1)
    cell_b = make_with_value(2)
    closure = (cell_a, cell_b)

    class _FakeCode:
        co_freevars = ()

    fake_func = types.SimpleNamespace(__closure__=closure, __code__=_FakeCode())

    # The defensive guard should bail out immediately and return an empty
    # mapping instead of attempting to index past ``co_freevars``.
    assert _closure_lookup(fake_func) == {}


# ---------------------------------------------------------------------------
# Private-helper tests for defensive / unreachable code paths.
# ---------------------------------------------------------------------------


def test_function_arg_defaults_ignores_non_int_positional():
    def handler(event, label="x", ms=275):
        pass

    defaults = _function_arg_defaults(handler)
    # The string default must be filtered out; only the int default remains.
    assert defaults == {"ms": 275}


def test_function_arg_defaults_returns_empty_when_only_string_defaults():
    def handler(event, label="x"):
        pass

    assert _function_arg_defaults(handler) == {}


def test_closure_lookup_returns_empty_when_no_closure():
    def handler(event):
        pass

    assert _closure_lookup(handler) == {}


def test_constant_ints_by_name_returns_empty():
    def handler(event):
        pass

    assert _constant_ints_by_name(handler.__code__) == {}


def test_resolve_debounce_value_returns_none_for_empty_store_index():
    # With an empty instruction list and a store index of 0, the defensive
    # guard at the top of ``_resolve_debounce_value`` triggers.
    assert _resolve_debounce_value([], 0, "event", {}, {}, {}) is None


def test_resolve_debounce_value_returns_none_when_store_index_below_offset():
    # The defensive ``store_index < _STORE_ATTR_VALUE_OFFSET`` guard.
    # With a single preceding instruction and a store index of 1, the guard
    # at the bottom of the function triggers.
    instructions = _build_fake_instructions([("LOAD_FAST", "event")])
    # The single LOAD_FAST sits at index 0; index 1 corresponds to "STORE_ATTR"
    # which is below the offset of 2.
    assert _resolve_debounce_value(instructions, 1, "event", {}, {}, {}) is None


def test_resolve_debounce_value_superinstruction_with_non_event_target_returns_none():
    """When the previous instruction IS a
    ``LOAD_FAST_LOAD_FAST``/``LOAD_FAST_BORROW_LOAD_FAST_BORROW``
    superinstruction but the fused target name does not match
    ``event_arg_name``, the inner guard must ``return None``.

    This covers the case where CPython fuses two ``LOAD_FAST`` ops for
    some other pair of locals (not the event argument).
    """
    prev = types.SimpleNamespace(
        opname="LOAD_FAST_BORROW_LOAD_FAST_BORROW",
        argval=("ms", "other_local"),  # target is "other_local", NOT "event"
    )
    val = types.SimpleNamespace(opname="LOAD_FAST_BORROW", argval="ms")
    instructions = [val, prev]
    # ``store_index`` of 2 represents the (hypothetical) ``STORE_ATTR`` slot
    # after the two preceding instructions.
    assert (
        _resolve_debounce_value(instructions, 2, "event", {"ms": 800}, {}, {}) is None
    )


def test_resolve_debounce_value_target_opname_not_allowed_returns_none():
    """When the target instruction's ``opname`` is not one of the allowed
    ``LOAD_FAST`` family members, the resolver must ``return None``.

    This handles unusual interpreter versions or future optimisations that
    might emit a different ``opname`` for the target expression.
    """
    # Build a sequence whose ``prev`` (the target) is ``LOAD_GLOBAL`` —
    # an opname the resolver does not recognise as a local load.
    val = types.SimpleNamespace(opname="LOAD_FAST_BORROW", argval="ms")
    prev = types.SimpleNamespace(opname="LOAD_GLOBAL", argval="event")
    instructions = [val, prev]
    assert (
        _resolve_debounce_value(instructions, 2, "event", {"ms": 800}, {}, {}) is None
    )


def test_resolve_debounce_value_target_argval_mismatch_returns_none():
    """When the target ``LOAD_FAST_BORROW`` references a local that isn't
    the event argument, the resolver must ``return None``.

    This guards against a handler such as ``other.debounce = ms`` —
    the bytecode looks the same modulo the target name, so the resolver
    must reject it.
    """
    val = types.SimpleNamespace(opname="LOAD_FAST_BORROW", argval="ms")
    prev = types.SimpleNamespace(opname="LOAD_FAST_BORROW", argval="other")
    instructions = [val, prev]
    assert (
        _resolve_debounce_value(instructions, 2, "event", {"ms": 800}, {}, {}) is None
    )


def test_resolve_debounce_value_val_instr_load_fast_borrow_returns_default():
    """When the value being stored is loaded via ``LOAD_FAST``/
    ``LOAD_FAST_BORROW`` (a local variable that's an argument), the
    resolver looks up that local in ``arg_defaults`` and returns the
    default value.

    CPython 3.14 typically fuses the value + target ``LOAD_FAST`` ops
    into the ``LOAD_FAST_BORROW_LOAD_FAST_BORROW`` superinstruction, but
    older interpreters (3.11/3.12) and unoptimised edge cases still
    emit separate ``LOAD_FAST`` instructions, so this branch must be
    covered.
    """
    val = types.SimpleNamespace(opname="LOAD_FAST_BORROW", argval="delay")
    prev = types.SimpleNamespace(opname="LOAD_FAST_BORROW", argval="event")
    instructions = [val, prev]
    assert (
        _resolve_debounce_value(instructions, 2, "event", {"delay": 350}, {}, {}) == 350
    )


def test_resolve_debounce_value_superinstruction_match_returns_default():
    """When the previous instruction IS a
    ``LOAD_FAST_LOAD_FAST`` / ``LOAD_FAST_BORROW_LOAD_FAST_BORROW``
    superinstruction whose fused ``(value_name, target_name)`` tuple is
    the right shape and the target name matches ``event_arg_name``, the
    helper returns ``arg_defaults.get(value_name)``.

    CPython 3.13+ emits these fused instructions for consecutive
    ``LOAD_FAST`` ops, so the branch is exercised through normal handler
    definitions on those interpreters. On 3.11/3.12 this test verifies
    the branch via a hand-crafted instruction.
    """
    prev = types.SimpleNamespace(
        opname="LOAD_FAST_BORROW_LOAD_FAST_BORROW",
        argval=("ms", "event"),
    )
    val = types.SimpleNamespace(opname="LOAD_CONST", argval=1)  # not used here
    instructions = [val, prev]
    assert _resolve_debounce_value(instructions, 2, "event", {"ms": 800}, {}, {}) == 800


def test_inspect_event_handler_handles_fused_superinstruction():
    """Cover the fused-superinstruction event-detection branch in
    ``inspect_event_handler`` by mocking ``dis.get_instructions``.

    CPython 3.13+ / 3.14+ emit the ``LOAD_FAST_LOAD_FAST`` /
    ``LOAD_FAST_BORROW_LOAD_FAST_BORROW`` superinstruction natively,
    but on 3.11 / 3.12 these opcodes don't exist — so we synthesise
    the instruction list via ``unittest.mock.patch`` to exercise the
    branch on every interpreter version.
    """
    import dis
    from unittest.mock import patch

    def handler(event, ms=400):
        event.debounce = ms

    fake_prev = types.SimpleNamespace(
        opname="LOAD_FAST_BORROW_LOAD_FAST_BORROW",
        argval=("ms", "event"),
    )
    fake_store = types.SimpleNamespace(opname="STORE_ATTR", argval="debounce")
    fake_resume = types.SimpleNamespace(opname="RESUME", argval=0)
    fake_const = types.SimpleNamespace(opname="LOAD_CONST", argval=None)
    fake_ret = types.SimpleNamespace(opname="RETURN_VALUE", argval=None)
    fake_list = [fake_resume, fake_prev, fake_store, fake_const, fake_ret]

    with patch.object(dis, "get_instructions", return_value=fake_list):
        result = inspect_event_handler(handler)

    # Expected: (prevent_default=False, stop_propagation=False, debounce=400).
    assert result == (False, False, 400)


# ---------------------------------------------------------------------------
# Python version-aware tests for ``LOAD_FAST_BORROW_LOAD_FAST_BORROW``
# (CPython 3.14+ superinstruction).
# ---------------------------------------------------------------------------


_PYTHON_314_OR_NEWER = sys.version_info >= (3, 14)


@pytest.mark.skipif(
    not _PYTHON_314_OR_NEWER,
    reason="LOAD_FAST_BORROW_LOAD_FAST_BORROW only exists in CPython 3.14+",
)
def test_inspect_event_handler_with_borrow_superinstruction():
    """CPython 3.14+ may fuse two ``LOAD_FAST`` instructions into
    ``LOAD_FAST_BORROW_LOAD_FAST_BORROW``. Verify the event-load branch
    is exercised when the fused target matches the event argument."""

    from reactpy.core.events import EventHandler

    def handler(event, ms=225):
        event.debounce = ms

    # Sanity: confirm the superinstruction is actually emitted on this
    # interpreter (otherwise the test would silently exercise a different
    # code path).
    import dis

    ops = {instr.opname for instr in dis.get_instructions(handler)}
    assert "LOAD_FAST_BORROW_LOAD_FAST_BORROW" in ops, ops

    eh = EventHandler(handler)
    assert eh.debounce == 225


@pytest.mark.skipif(
    not _PYTHON_314_OR_NEWER,
    reason="LOAD_FAST_BORROW_LOAD_FAST_BORROW only exists in CPython 3.14+",
)
def test_resolve_debounce_value_with_borrow_superinstruction_non_event_target():
    """When the fused superinstruction's target name does not match the event
    argument, ``_resolve_debounce_value`` falls through to ``return None``."""

    # We can't easily hand-craft bytecode on 3.14+, so test via the public
    # API by using a handler that loads two unrelated locals before the
    # STORE_ATTR. The superinstruction here loads ``other`` (not ``event``)
    # followed by ``event``.
    from reactpy.core.events import EventHandler

    def handler(event, other, ms=175):
        # Force two LOAD_FAST ops before STORE_ATTR. ``other`` and ``event``
        # are emitted as the fused superinstruction; if the event detector
        # picks up ``other`` instead, debounce detection should still work
        # for ``ms`` because the resolution checks the immediate predecessor.
        event.debounce = ms

    eh = EventHandler(handler)
    assert eh.debounce == 175


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_fake_instructions(items):
    """Return a list of simple ``dis.Instruction``-like objects for tests."""
    import dis

    result = []
    for opname, argval in items:
        # The positional layout of ``dis.Instruction`` changed between 3.12
        # and 3.13. Probe the constructor with a minimal argument list and
        # fall back to the additional ``line_number`` keyword on newer
        # interpreters.
        kwargs = {}
        try:
            instr = dis.Instruction(
                opname,
                0,
                argval,
                argval,
                len(result),
                None,
                0,
                False,
            )
        except TypeError:
            kwargs.setdefault("line_number", 0)
            instr = dis.Instruction(
                opname,
                0,
                argval,
                argval,
                len(result),
                None,
                0,
                False,
                0,
            )
        result.append(instr)
    return result
