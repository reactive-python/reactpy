import abc
import asyncio
from concurrent.futures import Executor
import inspect
from functools import wraps
import time
from typing import (
    TYPE_CHECKING,
    Dict,
    Callable,
    Any,
    List,
    Optional,
    overload,
    Awaitable,
    Union,
    overload,
)


if TYPE_CHECKING:  # pragma: no cover
    from .layout import AbstractLayout
    from .vdom import VdomDict  # noqa


ElementConstructor = Callable[..., "Element"]
ElementRenderFunction = Callable[..., Awaitable["VdomDict"]]


@overload
def element(
    function: Callable[..., Any],
    *,
    state: Optional[str] = None,
    run_in_executor: Union[bool, Executor] = False,
) -> ElementConstructor:
    ...


@overload
def element(
    *, state: Optional[str] = None, run_in_executor: Union[bool, Executor] = False
) -> Callable[[ElementRenderFunction], ElementConstructor]:
    ...


def element(
    function: Optional[ElementRenderFunction] = None,
    state: Optional[str] = None,
    run_in_executor: Union[bool, Executor] = False,
) -> Callable[..., Any]:
    """A decorator for defining an :class:`Element`.

    Parameters:
        function:
            The function that will render a :term:`VDOM` model.
        state:
            A comma seperated string of function parameters that should be retained
            across updates unless explicitely changed when calling :meth:`Element.update`.
        run_in_executor:
            Whether or not to run the given ``function`` in a background thread. This is
            useful for long running and blocking operations that might prevent other
            elements from rendering in the meantime.
    """

    def setup(func: ElementRenderFunction) -> ElementConstructor:

        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"Expected a coroutine function, not {func}")

        @wraps(func)
        def constructor(*args: Any, **kwargs: Any) -> Element:
            element = Element(func, state, run_in_executor)
            element.update(*args, **kwargs)
            return element

        return constructor

    if function is not None:
        return setup(function)
    else:
        return setup


class AbstractElement(abc.ABC):

    __slots__ = ["_layout"]

    if not hasattr(abc.ABC, "__weakref__"):
        __slots__.append("__weakref__")

    def __init__(self) -> None:
        self._layout: Optional["AbstractLayout"] = None

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return str(id(self))

    @abc.abstractmethod
    async def render(self) -> Any:
        """Return the model for the element."""
        ...

    async def mount(self, layout: "AbstractLayout") -> None:
        """Mount a layout to the element instance.

        Occurs just before rendering the element for the **first** time.
        """
        self._layout = layout

    async def unmount(self) -> None:
        """Unmount the current layout from the element instance.

        Occurs just before the element is removed from view.
        """
        self._layout = None

    # FIXME: https://github.com/python/mypy/issues/5876
    update: Callable[..., Any]

    def update(self) -> None:  # type: ignore
        """Schedule this element to be rendered again soon."""
        if self._layout is not None:
            self._layout.update(self)


# animation stop callback
_STP = Callable[[], None]
# type for animation function of element
_ANM = Callable[[_STP], Awaitable[bool]]


class Element(AbstractElement):
    """An object for rending element models.

    Rendering element objects is typically done by a :class:`idom.core.layout.Layout` which
    will :meth:`Element.mount` itself to the element instance the first time it is rendered.
    From there an element instance will communicate its needs to the layout. For example
    when an element wants to re-render it will call :meth:`idom.core.layout.Layout.element_updated`.

    The lifecycle of an element typically goes in this order:

    1. The element instance is instantiated.

    2. The element's layout will mount itself.

    3. The layout will call :meth:`Element.render`.

    4. The element is dormant until an :meth:`Element.update` occurs.

    5. Go back to step **3**.
    """

    __slots__ = (
        "_animation_futures",
        "_function",
        "_function_signature",
        "_cross_update_state",
        "_cross_update_parameters",
        "_state",
        "_state_updated",
        "_run_in_executor",
    )

    def __init__(
        self,
        function: ElementRenderFunction,
        state_parameters: Optional[str],
        run_in_executor: Union[bool, Executor] = False,
    ):
        super().__init__()
        self._function = function
        self._function_signature = inspect.signature(function)
        self._layout: Optional["AbstractLayout"] = None
        self._cross_update_state: Dict[str, Any] = {}
        self._cross_update_parameters: List[str] = list(
            map(str.strip, (state_parameters or "").split(","))
        )
        self._state: Dict[str, Any] = {}
        self._state_updated: bool = False
        self._animation_futures: List[asyncio.Future[None]] = []
        self._run_in_executor = run_in_executor

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Schedule this element to render with new parameters."""
        if not self._state_updated:
            # only tell layout to render on first update call
            self._state = {}
            self._state_updated = True
            self._cancel_animation()
            super().update()
        bound = self._function_signature.bind_partial(None, *args, **kwargs)
        self._state.update(list(bound.arguments.items())[1:])

    @overload
    def animate(self, function: _ANM, rate: float = 0) -> _ANM:
        ...

    @overload
    def animate(self, *, rate: float = 0) -> Callable[[_ANM], _ANM]:
        ...

    def animate(
        self, function: Optional[_ANM] = None, rate: float = 0
    ) -> Callable[..., Any]:
        """Schedule this function to run soon, and then render any updates it caused."""

        def setup(function: _ANM) -> _ANM:
            pacer = FramePacer(rate)

            async def animation() -> None:
                while True:
                    await function(cancel_animation_future)
                    # we need another await here in order to catch
                    # a cancellation call (not sure why though)
                    await pacer.wait()

            # we store this future for later so we can cancel it
            future = asyncio.ensure_future(animation())

            # stops the animation loop.
            def cancel_animation_future() -> None:
                future.cancel()

            self._animation_futures.append(future)

            return function

        if function is None:
            return setup
        else:
            return setup(function)

    async def render(self) -> Any:
        """Render the element's :term:`VDOM` model."""
        # animations from the previous render should stop
        await self._stop_animation()

        # load update and reset for next render
        state = self._state

        if state is None:
            raise RuntimeError(f"{self} cannot render - element has no state.")

        for name in self._cross_update_parameters:
            if name not in state:
                if name in self._cross_update_state:
                    state[name] = self._cross_update_state[name]
            else:
                self._cross_update_state[name] = state[name]

        self._state_updated = False

        if self._run_in_executor is False:
            return await self._function(self, **state)
        else:
            loop = asyncio.get_event_loop()
            # use default executor if _run_in_executor was only given as True
            exe = None if self._run_in_executor is True else self._run_in_executor
            # run the function in a new thread so we don't block
            return await loop.run_in_executor(exe, self._render_in_executor, state)

    async def unmount(self) -> None:
        await self._stop_animation()
        await super().unmount()

    def _cancel_animation(self) -> None:
        for f in self._animation_futures:
            f.cancel()

    async def _stop_animation(self) -> None:
        self._cancel_animation()
        futures = self._animation_futures[:]
        self._animation_futures.clear()
        try:
            await asyncio.gather(*futures)
        except asyncio.CancelledError:
            pass

    def _render_in_executor(self, state: Dict[str, Any]) -> Any:
        # we need to set up the event loop since we'll be in a new thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._function(self, **state))
        finally:
            loop.close()
        return result

    def __repr__(self) -> str:
        qualname = getattr(self._function, "__qualname__", None)
        if qualname is not None:
            return "%s(%s)" % (qualname, self.id)
        else:
            return "%s(%r, %r)" % (type(self).__name__, self._function, self.id)


class FramePacer:
    """Simple utility for pacing frames in an animation loop."""

    def __init__(self, rate: float):
        self._rate = rate
        self._last = time.time()

    async def wait(self) -> None:
        await asyncio.sleep(self._rate - (time.time() - self._last))
        self._last = time.time()
