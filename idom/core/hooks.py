from typing import TypeVar, Tuple, Callable, Dict, Any, List

from .element import Element


_State = TypeVar("_State")
_global_state: Dict[str, List[Any]] = {}


def use_state(default: _State) -> Tuple[_State, Callable[[_State], None]]:
    element = Element.currently_rendering()
    hook_id = element.next_hook_id()

    if hook_id not in _global_state:
        _global_state[hook_id] = default

    def set_state(new: _State) -> None:
        _global_state[hook_id] = new
        element.update()

    return _global_state[hook_id], set_state
