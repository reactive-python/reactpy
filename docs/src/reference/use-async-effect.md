## Overview

<p class="intro" markdown>

`use_async_effect` is a ReactPy hook that lets you run an `#!python async def` effect, and keep it running across renders.

</p>

```python linenums="0"
use_async_effect(effect)
use_async_effect(effect, dependencies=[value])
```

---

## Reference

### `use_async_effect(effect, dependencies=..., shield=False)`

Call `use_async_effect` at the top level of your component to run an asynchronous effect. ReactPy wraps the coroutine in an `#!python asyncio.Task`, so it runs on the connection's event loop rather than blocking the render.

```python linenums="0"
from reactpy import use_async_effect
```

#### Parameters

-   **`effect`**: An `#!python async def` function taking **no arguments**. To run work in the background and stop it later, loop and handle cancellation — see [running a long-lived effect](#running-a-long-lived-effect).

-   **`dependencies`** *(optional)*: Same four-way meaning as in [`use_effect`](./use-effect.md), and the default is again *not* React's:

    | Value | Behaviour (verified) |
    | --- | --- |
    | omitted (`...`) | **Inferred** from the free variables of your closure. |
    | `#!python dependencies=[]` | Starts **once**, on mount. |
    | `#!python dependencies=[a, b]` | Restarts when the identity of `#!python a` or `#!python b` changes. |
    | `#!python dependencies=None` | Restarts after **every** render. |

-   **`shield`** *(optional)*: When `#!python True`, an in-flight effect is **not** cancelled when the component unmounts or the effect is superseded. Default `#!python False`.

#### Returns

`None` when given the effect, or a decorator when called without one.

#### Caveats

-   **The effect must take zero arguments.** ReactPy calls `#!python asyncio.create_task(func())` (`core/hooks.py`). The 1.x signature `#!python async def effect(stop):` is therefore broken — and it fails *silently*. Verified: the component renders normally, the model carries no error, the browser shows nothing wrong; the only trace is `Error in effect` / `TypeError: ... missing 1 required positional argument: 'stop'` in the **server** log. If your async effect "does nothing", check the server log first.
-   There is **no `stop` event** to wait on. Cancellation is ordinary `#!python asyncio.CancelledError`; a long-running effect should loop and break out of it.
-   Cancelling is also how clean-up happens: when dependencies change, the running task is cancelled before the new one starts.
-   The default dependency behaviour is inference, not "every render". See [`use_effect`](./use-effect.md) for the full table.
-   Effects run on the **server**. `#!python document` and `#!python window` do not exist.
-   An exception raised inside the coroutine is logged on the server only — no error reaches the model or the browser.
-   A new effect does not wait for the old one to finish unless you await cancellation, so two overlapping tasks can briefly run side by side. Use `#!python shield` deliberately, not by default.

---

## Usage

### Importing `use_async_effect`

```python linenums="0"
from reactpy import use_async_effect
```

### Running a one-shot async effect

For a single await — a request, a slow lookup — write the coroutine straight:

```python linenums="0"
@component
def stats(repo):
    data, set_data = use_state(None)

    async def effect():
        result = await fetch_stats(repo)
        set_data(result)

    use_async_effect(effect, dependencies=[repo])

    return html.p(data if data is not None else "loading...")
```

Setting state from the effect schedules the re-render; nothing else is needed.

### Running a long-lived effect

To keep work running across renders, loop and honour cancellation. This is what ReactPy's version of React's `#!js setInterval` example looks like:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_effect/async_clock/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The clock advances on its own — verified, one update per second. When `#!python dependencies` change or the component unmounts, ReactPy cancels the task and the loop exits through `#!python CancelledError`.

!!! warning "Do not wait for a `stop` event"

    ReactPy 1.x passed a `#!python stop` event into async effects. That parameter no longer exists, and passing it is **not** reported anywhere the user can see. Write this:

    ```python linenums="0"
    async def effect():
        while True:
            do_work()
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
    ```

    Not this:

    ```python linenums="0"
    async def effect(stop):  # 🚩 silent failure
        while not stop.is_set():
            ...
    ```

### Shielding an effect from cancellation

`#!python shield=True` lets an in-flight effect run to completion even as the component unmounts — useful for finishing a request whose result must not be discarded:

```python linenums="0"
use_async_effect(effect, dependencies=[], shield=True)
```

Verified: with `#!python shield=True` a sleeping effect reached its completion line after the layout exited; with the default it was cancelled at that same moment. Leave this off unless you specifically want work to outlive the component, since it also means the effect keeps holding references and consuming the loop.

### Cleanup

Async effects do not return a clean-up function; cancellation *is* the clean-up. Put teardown in the `#!python except asyncio.CancelledError` branch, and re-raise so asyncio can finish cancelling:

```python linenums="0"
async def effect():
    handle = open_connection()
    try:
        while True:
            await handle.poll()
    except asyncio.CancelledError:
        handle.close()
        raise
```

Re-raising matters: swallowing `#!python CancelledError` leaves the task in a state asyncio did not expect.

### Choosing between `use_effect` and `use_async_effect`

| Need | Use |
| --- | --- |
| A synchronous side effect | [`use_effect`](./use-effect.md) |
| Anything `#!python await`-based | `use_async_effect` |
| A repeating timer, polling, a subscription stream | `use_async_effect` with a loop |
| Work that must block the render | neither — do it during render, or raise |

Passing an `#!python async def` to `use_effect` fails loudly, which is the one mismatch ReactPy *does* report: `TypeError: use_effect does not support async functions. Use use_async_effect instead.`
