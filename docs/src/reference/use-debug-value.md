## Overview

<p class="intro" markdown>

`use_debug_value` is a ReactPy hook that writes a message to the server log whenever it changes, for the component that calls it.

</p>

```python linenums="0"
use_debug_value(message, dependencies)
```

ReactPy components run on the server, so there is no DevTools panel to label. This is the equivalent: a value that shows up in your server's log output, tagged with the component that produced it, printed only when it differs from the last thing printed.

!!! warning "It needs debug mode, and logs go to the server"
    Nothing happens unless `#!python REACTPY_DEBUG` is on. Set it before importing ReactPy — `#!python REACTPY_DEBUG=1 python app.py`, or `#!python os.environ["REACTPY_DEBUG"] = "1"` at the top of your entry point. Output goes through the standard `#!python logging` module under the `#!python reactpy.core.hooks` logger, so it lands wherever *your* logging configuration sends it, not in the browser console. A reader who expects DevTools will conclude the hook is broken; it is not.

---

## Reference

### `use_debug_value(message, dependencies)` { #use-debug-value }

Call it at the top level of a component, or at the top level of one of your own hooks.

```python linenums="0"
from reactpy import use_debug_value
```

#### Parameters

-   **`message`**: The value to log, **or** a function of no arguments that produces it. Pass a function when building the message costs something — ReactPy memoizes it, so it re-runs only when its dependencies change.
-   **`dependencies`**: Only meaningful with a function `#!python message`. Same three shapes as every other hook that takes them:

    | You pass                       | Meaning                                                       |
    | ------------------------------ | ------------------------------------------------------------- |
    | `#!python dependencies=[a, b]` | Rebuild the message when `#!python a` or `#!python b` changes. |
    | omitted (the default)          | Infer them from the function's closure.                        |
    | `#!python dependencies=None`   | Rebuild the message on every render.                           |

#### Returns

`#!python None`.

#### Caveats

-   **Silent without debug mode.** With `#!python REACTPY_DEBUG` off, the hook logs nothing. Whether it still *builds* the message is decided by the dependency comparison, not by debug mode: the message is produced through `#!python use_memo`, so a builder whose dependencies never change runs once and its result is discarded on every later render. A builder that closes over changing state runs every render, debug or no debug. If the build is expensive, control it with the dependency argument — do not assume the hook skipped it, and do not assume it ran.
-   **"Changed" means `!=`, not identity.** Unlike every other hook, which compares dependencies with `strictly_equal`, this one compares the new message against the previous one with plain `#!python !=`. So a freshly constructed `#!python {"kind": "rows"}` logs once and then stays quiet, because it compares equal to what was logged last time. Verified.
-   **The comparison runs on every render**, on the value you supply. For a large or slow-to-compare object that is a real cost, paid whether or not anything gets logged. This is the one hook where the docstring's performance note is worth taking literally.
-   **An uncomparable message breaks the component.** If `#!python message != previous` raises, the exception is not caught: it surfaces as a render error in the model. A class with a `#!python __eq__` that raises will fail the component, so keep messages to plain data — strings, numbers, dicts, lists.
-   **The value is memoized like any other hook value.** With a stable message, the builder function runs once; with a message that changes each render, it runs each render. Measured across four renders: stable → 1 call, changing → 4 calls.
-   Like every hook, call it **only at the top level** — never in a loop, a conditional, or after an early `#!python return`.

---

## Usage

### Labelling a custom hook

The useful case. When a component calls three of your own hooks, a log line that says only `shop(...)` tells you nothing; a message naming what the hook holds tells you which hook is behaving oddly, and when.

Run this with debug on and press **Add item**. Each add logs one line through the `#!python reactpy.core.hooks` logger, prefixed with the component and its id:

```text
shop(7f7ef6f0d540) 0 item(s): -
shop(7f7ef6f0d540) 1 item(s): item 1
shop(7f7ef6f0d540) 2 item(s): item 1, item 2
shop(7f7ef6f0d540) 3 item(s): item 1, item 2, item 3
```

Pressing a button that leaves the cart alone logs nothing, because the message did not change.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_debug_value/custom_hook/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

### Passing a function as the message

If producing the message is more than string formatting, pass a function and let ReactPy memoize it. The report below finds the highest score to build its label; that walk happens once per distinct `#!python rows`, not once per render.

Run it with debug on and press **Add row**:

```text
report(7f7ef6f0da80) 1 rows, best=ada:91
report(7f7ef6f0da80) 2 rows, best=ada:91
report(7f7ef6f0da80) 3 rows, best=ada:91
```

=== "app.py"

    ```python
    {% include "../../examples/reference_use_debug_value/expensive_message/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Keep the message honest about what it reads. A function that reads no state is computed once and then logs nothing ever again, which usually reads as "the hook stopped working" rather than as correct memoization.

---

## Troubleshooting

### Nothing is logged

Almost always debug mode. The `#!python REACTPY_DEBUG` *environment* variable is read when `#!python reactpy.config` is first imported, so setting `#!python os.environ` after ReactPy is already imported has no effect — start the process with `#!python REACTPY_DEBUG=1`, or set the variable before importing anything from `#!python reactpy`.

The option object can also be flipped at any point, which is the version that works from inside a test or a REPL:

```python linenums="0"
from reactpy.config import REACTPY_DEBUG

REACTPY_DEBUG.current = True
```

If debug is on and you still see nothing, the logger is being filtered. ReactPy logs at `DEBUG` level under `#!python reactpy.core.hooks`; a configuration that shows only warnings will hide these lines.

### It logs on every render

Your message changes every render. A timestamp, `#!python id(self)`, a freshly built object compared by identity, or a counter you increment during rendering all do this. Make the message describe *state* rather than the render.

### It stopped logging

The message has not changed since the last line, which is the hook working as designed. If you expected a change, either the value genuinely did not change or your function is memoized on dependencies that never move — pass `#!python dependencies=None` briefly to confirm which.

### My component fails to render after adding it

You passed something whose `#!python !=` raises. The comparison is not guarded, so the exception becomes a render error. Pass plain data instead, and format it lazily in a function if it is large.
