from queue import Queue
from threading import Event

import pytest

import idom
from idom.client.utils import Spinner


def test_spinner_custom_display():
    displayed_frames = Queue()

    def save_display(frame, text):
        displayed_frames.put((frame, text))

    spinner = Spinner(
        "my spinner",
        frames=[".  ", ".. ", "..."],
        success_frame="success",
        failure_frame="failure",
        rate=0,  # go as fast as we can
        display=save_display,
    )

    seen_frames = set()
    with spinner:
        while True:
            frame = displayed_frames.get()
            if frame in seen_frames:
                break
            seen_frames.add(frame)
    # grab the success frame
    while not displayed_frames.empty():
        seen_frames.add(displayed_frames.get())

    assert seen_frames == {
        (".  ", "my spinner"),
        (".. ", "my spinner"),
        ("...", "my spinner"),
        ("success", "my spinner"),
        (None, "my spinner"),
    }

    seen_frames = set()

    with pytest.raises(ValueError, match="we raised this on purpose"):
        with spinner:
            while True:
                frame = displayed_frames.get()
                if frame in seen_frames:
                    raise ValueError("we raised this on purpose")
                seen_frames.add(frame)
    # grab the failure frame
    while not displayed_frames.empty():
        seen_frames.add(displayed_frames.get())

    assert seen_frames == {
        (".  ", "my spinner"),
        (".. ", "my spinner"),
        ("...", "my spinner"),
        ("failure", "my spinner"),
        (None, "my spinner"),
    }


def test_spinner_is_running_in_notebook(mocker):
    spinner = Spinner("my spinner")

    assert spinner._running_in_notebook() is False

    class FakeIpython:
        config = {}

    mocker.patch("IPython.get_ipython", return_value=FakeIpython())

    assert spinner._running_in_notebook() is False

    class FakeIpythonWithKernel:
        config = {"IPKernelApp": "a-kernel-for-ipython"}

    mocker.patch("IPython.get_ipython", return_value=FakeIpythonWithKernel())

    assert spinner._running_in_notebook() is True


def test_spinner_display_terminal(capsys):
    done = Event()
    display_count = idom.Ref(0)

    class MySpinner(Spinner):
        def _display_terminal(self, frame, text):
            if display_count.current < 3 or frame in (
                self.success_frame,
                self.failure_frame,
                None,
            ):
                super()._display_terminal(frame, text)
                display_count.current += 1
            else:
                done.set()

    spinner = MySpinner(
        "my spinner",
        frames=[".  ", ".. ", "..."],
        success_frame="success",
        failure_frame="failure",
        rate=0,
    )

    with spinner:
        done.wait()

    captured = capsys.readouterr()
    expected = ".   my spinner\x1b[K\r..  my spinner\x1b[K\r... my spinner\x1b[K\rsuccess my spinner\x1b[K\r\n"
    assert captured.out == expected


def test_spinner_display_notebook(mocker):
    done = Event()
    display_count = idom.Ref(0)

    class MySpinner(Spinner):
        def _display_notebook(self, frame, text):
            if display_count.current < 3 or frame in (
                self.success_frame,
                self.failure_frame,
                None,
            ):
                super()._display_notebook(frame, text)
                display_count.current += 1
            else:
                done.set()

        @staticmethod
        def _running_in_notebook():
            return True

    displays = []

    class Handle:
        def update(self, value):
            displays.append(value._repr_html_())

    mocker.patch("IPython.display.display", side_effect=lambda *a, **kw: Handle())

    spinner = MySpinner(
        "my spinner",
        frames=[".  ", ".. ", "..."],
        success_frame="success",
        failure_frame="failure",
        rate=0,
    )

    with spinner:
        done.wait()

    assert displays == [
        "<pre><code>.   my spinner<code></pre>",
        "<pre><code>..  my spinner<code></pre>",
        "<pre><code>... my spinner<code></pre>",
        "<pre><code>success my spinner<code></pre>",
    ]
