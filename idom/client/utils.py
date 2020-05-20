import time
from threading import Thread, Event
from types import TracebackType
from typing import Dict, Sequence, Any, Optional, Type, Callable


class Spinner:

    __slots__ = (
        "text",
        "frames",
        "rate",
        "display",
        "state",
        "failure_frame",
        "success_frame",
        "_stop",
        "_stopped",
    )

    def __init__(
        self,
        text: str,
        frames: Sequence[str] = "|/-\\",
        failure_frame: str = "✖",
        success_frame: str = "✔",
        rate: float = 0.1,
        display: Optional[Callable[[Optional[str], str], None]] = None,
    ) -> None:
        self.text = text
        self.frames = frames
        self.failure_frame = failure_frame
        self.success_frame = success_frame
        self.rate = rate
        self._stop = Event()
        self._stopped = Event()
        if display is not None:
            self.display = display
        else:
            self.display = (
                self._display_notebook
                if self._running_in_notebook()
                else self._display_terminal
            )
        self.state: Dict[str, Any] = {}

    def __enter__(self) -> None:
        self._stop.clear()
        self._stopped.clear()
        self._animate()
        return None

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._stop.set()
        self._stopped.wait()
        if exc_val is not None:
            self.display(self.failure_frame, self.text)
        else:
            self.display(self.success_frame, self.text)
        self.display(None, self.text)
        return None

    def _animate(self) -> None:
        def run() -> None:
            index = 0
            while not self._stop.is_set():
                self.display(self.frames[index], self.text)
                index = (index + 1) % len(self.frames)
                time.sleep(self.rate)
            self._stopped.set()
            return None

        Thread(target=run, daemon=True).start()

        return None

    def _display_notebook(self, frame: Optional[str], text: str) -> None:
        if frame is not None:
            from IPython.display import HTML, display

            if "view" not in self.state:
                self.state["view"] = display(display_id=True)

            html = HTML(f"<pre><code>{frame} {text}<code></pre>")
            self.state["view"].update(html)

        return None

    def _display_terminal(self, frame: Optional[str], text: str) -> None:
        if frame is not None:
            print(f"{frame} {text}\033[K", end="\r")
        else:
            print()
        return None

    @staticmethod
    def _running_in_notebook() -> bool:
        try:
            from IPython import get_ipython

            ipython_instance = get_ipython()
            if ipython_instance is None:
                return False
            if "IPKernelApp" not in ipython_instance.config:
                return False
        except ImportError:  # pragma: no cover
            return False
        return True
