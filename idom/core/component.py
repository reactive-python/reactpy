import abc
import inspect
from functools import wraps
from typing import TYPE_CHECKING, Dict, Callable, Any, Tuple, Union
from weakref import ReferenceType

from .hooks import LifeCycleHook

if TYPE_CHECKING:  # pragma: no cover
    from .vdom import VdomDict  # noqa


ComponentConstructor = Callable[..., "Component"]
ComponentRenderFunction = Callable[..., Union["AbstractComponent", "VdomDict"]]


def component(function: ComponentRenderFunction) -> Callable[..., "Component"]:
    """A decorator for defining an :class:`Component`.

    Parameters:
        function:
            The function that will render a :ref:`VDOM <VDOM Mimetype>` model.
    """

    @wraps(function)
    def constructor(*args: Any, **kwargs: Any) -> Component:
        return Component(function, args, kwargs)

    return constructor


class AbstractComponent(abc.ABC):
    """A base class for all component implementations"""

    __slots__ = ["_life_cycle_hook"]
    if not hasattr(abc.ABC, "__weakref__"):
        __slots__.append("__weakref__")

    # When a LifeCyleHook is created it will bind a WeakReference of itself to the its
    # component. This is only useful for class-based component implementations. For
    # functional components, the LifeCycleHook is accessed by getting the current_hook().
    _life_cycle_hook: "ReferenceType[LifeCycleHook]"

    @abc.abstractmethod
    def render(self) -> "VdomDict":
        """Render the component's :ref:`VDOM <VDOM Mimetype>` model."""

    def schedule_render(self):
        """Schedule a re-render of this component

        This is only used by class-based component implementations. Most components
        should be functional components that use hooks to schedule renders and save
        state.
        """
        try:
            hook = self._life_cycle_hook()
        except AttributeError:
            raise RuntimeError(
                f"Component {self} has no hook. Are you rendering in a layout?"
            )
        else:
            assert hook is not None, f"LifeCycleHook for {self} no longer exists"
            hook.schedule_render()


class Component(AbstractComponent):
    """A functional component"""

    __slots__ = (
        "_function",
        "_args",
        "_kwargs",
    )

    def __init__(
        self,
        function: ComponentRenderFunction,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def render(self) -> Any:
        return self._function(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        sig = inspect.signature(self._function)
        args = sig.bind(*self._args, **self._kwargs).arguments
        items = ", ".join(f"{k}={v!r}" for k, v in args.items())
        if items:
            return f"{self._function.__name__}({hex(id(self))}, {items})"
        else:
            return f"{self._function.__name__}({hex(id(self))})"
