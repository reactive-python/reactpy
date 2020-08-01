from functools import lru_cache
from threading import get_ident as get_thread_id
from typing import (
    Dict,
    Any,
    TypeVar,
    Callable,
    Tuple,
    Optional,
    Generic,
    Union,
    List,
)

from .element import AbstractElement


__all__ = [
    "use_update",
    "use_state",
    "use_memo",
    "use_lru_cache",
]


def use_update() -> Callable[[], None]:
    return current_hook().use_update()


_StateType = TypeVar("_StateType")


class Shared(Generic[_StateType]):

    __slots__ = "_callbacks", "_value"

    def __init__(self, value: _StateType) -> None:
        self._callbacks: Dict[str, Callable[[_StateType], None]] = {}
        self._value = value

    def update(self, value: _StateType) -> None:
        self._value = value
        for cb in self._callbacks.values():
            cb(value)


def _new_is_not_old(old: _StateType, new: _StateType) -> bool:
    return new is not old


def use_state(
    value: Union[_StateType, Shared[_StateType]],
    should_update: Callable[[_StateType, _StateType], bool] = _new_is_not_old,
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    if isinstance(value, Shared):
        return _use_shared(value, should_update)
    else:
        return _use_state(value, should_update)


def _use_shared(
    shared: Shared[_StateType], should_update: Callable[[_StateType, _StateType], bool],
) -> [_StateType, Callable[[_StateType], None]]:
    hook = current_hook()
    update = hook.use_update()

    hook.use_finalize(shared._callbacks.pop, hook.element_id, None)
    old = shared._value
    shared._callbacks[hook.element_id] = (
        lambda new: update() if should_update(new, old) else None
    )

    def set_state(new: _StateType) -> None:
        shared.update(new)

    return shared._value, set_state


def _use_state(
    value: _StateType, should_update: Callable[[_StateType, _StateType], bool],
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    hook = current_hook()
    state: Dict[str, Any] = hook.use_state(dict)
    update = hook.use_update()

    if "value" not in state:
        state["value"] = value

    def set_state(new: _StateType) -> None:
        old = state["value"]
        if should_update(new, old):
            state["value"] = new
            update()

    return state["value"], set_state


_MemoValue = TypeVar("_MemoValue")


def use_memo(*args: Any) -> Callable[[Callable[[], _MemoValue]], _MemoValue]:
    def use_setup(function: Callable[[], _MemoValue]) -> _MemoValue:
        hook = current_hook()
        cache: Dict[int, _MemoValue] = hook.use_state(dict)

        key = hash(args)
        if key in cache:
            result = cache[key]
        else:
            cache.clear()
            result = cache[key] = function()

        return result

    return use_setup


_LruFunc = TypeVar("_LruFunc")


def use_lru_cache(
    function: _LruFunc, maxsize: Optional[int] = 128, typed: bool = False
) -> _LruFunc:
    return current_hook().use_state(lru_cache(maxsize, typed), function)


_current_life_cycle_hook: Dict[int, "LifeCycleHook"] = {}


def current_element() -> AbstractElement:
    # this is primarilly used for testing
    return current_hook()._element


def current_hook() -> "LifeCycleHook":
    try:
        return _current_life_cycle_hook[get_thread_id()]
    except KeyError as error:
        msg = "No life cycle hook is active. Are you rendering in a layout?"
        raise RuntimeError(msg) from error


class LifeCycleHook:

    __slots__ = (
        "_element",
        "_schedule_render",
        "_current_state_index",
        "_state",
        "_did_update",
        "_has_rendered",
        "_finalizers",
        "__weakref__",
    )

    def __init__(
        self,
        element: AbstractElement,
        schedule_render: Callable[[AbstractElement], None],
    ) -> None:
        self._element = element
        self._schedule_render = schedule_render
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._finalizers: List[Callable[[], None]] = []
        self._did_update = False
        self._has_rendered = False

    @property
    def element_id(self):
        return self._element.id

    def use_update(self):
        def update() -> None:
            if not self._did_update:
                self._did_update = True
                self._schedule_render(self._element)
            return None

        return update

    def use_state(
        self, _function_: Callable[..., _StateType], *args: Any, **kwargs: Any
    ) -> _StateType:
        if not self._has_rendered:
            # since we're not intialized yet we're just appending state
            result = _function_(*args, **kwargs)
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result

    def use_finalize(
        self, _function_: Callable[..., None], *args: Any, **kwargs: Any
    ) -> None:
        if not args and not kwargs:
            self._finalizers.append(_function_)
        else:
            self._finalizers.append(lambda: _function_(*args, **kwargs))

    def set_current(self):
        _current_life_cycle_hook[get_thread_id()] = self

    def unset_current(self):
        # use an assert here for debug purposes since this should never be False
        assert _current_life_cycle_hook.pop(get_thread_id()) is self

    def element_will_render(self) -> None:
        self._did_update = False
        self._current_state_index = 0
        self._finalizers.clear()

    def element_did_render(self) -> None:
        self._has_rendered = True

    def element_will_unmount(self) -> None:
        ...
