## Overview

<p class="intro" markdown>

State variables might look like regular Python variables that you can read and write to. However, state behaves more like a snapshot. Setting it does not change the state variable you already have, but instead triggers a re-render.

</p>

!!! summary "You will learn"

    -   How setting state triggers renders
    -   Why variable and prop values are fixed when a render is started
    -   Why event handlers see old values of state

## Setting state triggers renders

You might think of your user interface as changing directly in response to the user event like a click. In ReactPy, it works a little differently from this mental model. You have already seen that [setting state requests a re-render](./render-and-commit.md#step-1-trigger-a-render). This means that for an interface to react to an event, you need to _update the state_.

In this example, when you press "send", `#!python set_is_sent(True)` tells ReactPy to re-render the UI:

=== "app.py"

    ```python
    {% include "../../examples/state_as_a_snapshot/triggers_renders/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_as_a_snapshot/triggers_renders/styles.css" %}
    ```

=== ":material-play: Run"

Here's what happens when you click the button:

1. The `#!python onSubmit` event handler executes.
2. `#!python set_is_sent(True)` sets `#!python is_sent` to `#!python True` and queues a new render.
3. ReactPy re-renders the component according to the new `#!python is_sent` value.

Let's take a closer look at the relationship between state and rendering.

## Rendering takes a snapshot in time

["Rendering"](./render-and-commit.md#step-2-reactpy-renders-your-components) means that ReactPy is calling your component, which is a function. The VDOM you return from that function is like a snapshot of the UI in time. Its props, event handlers, and local variables were all calculated **using its state at the time of the render.**

Unlike a photograph or a movie frame, the UI "snapshot" you return is interactive. It includes logic like event handlers that specify what happens in response to inputs. ReactPy updates the screen to match this snapshot and connects the event handlers. As a result, pressing a button triggers the click handler from that snapshot.

When ReactPy re-renders a component:

1. ReactPy calls your function again.
2. Your function returns a new VDOM snapshot.
3. ReactPy then updates the screen to match the snapshot you've returned.

As a component's memory, state is not like a regular variable that disappears after your function returns. State actually "lives" in ReactPy itself — as if on a shelf! — outside of your function. When ReactPy calls your component, it gives you a snapshot of the state for that particular render. Your component returns a snapshot of the UI with a fresh set of props and event handlers, all calculated **using the state values from that render!**

Here's a little experiment to show you how this works. Clicking the "+3" button calls `#!python set_number(number + 1)` three times, so you might expect three increments.

=== "app.py"

    ```python
    {% include "../../examples/state_as_a_snapshot/snapshot_in_time/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_as_a_snapshot/snapshot_in_time/styles.css" %}
    ```

=== ":material-play: Run"

Notice that `#!python number` only increments once per click — verified by dispatching a click and reading the result.

**Setting state only changes it for the _next_ render.** During the first render, `#!python number` was `#!python 0`. This is why, in _that render's_ `#!python handle_click`, the value of `#!python number` is still `#!python 0` even after `#!python set_number(number + 1)` was called:

Here is what this button's click handler tells ReactPy to do:

1. `#!python set_number(number + 1)`: `#!python number` is `#!python 0`, so `#!python set_number(0 + 1)`.
    - ReactPy prepares to change `#!python number` to `#!python 1` on the next render.
2. `#!python set_number(number + 1)`: `#!python number` is `#!python 0`, so `#!python set_number(0 + 1)`.
    - ReactPy prepares to change `#!python number` to `#!python 1` on the next render.
3. `#!python set_number(number + 1)`: `#!python number` is `#!python 0`, so `#!python set_number(0 + 1)`.
    - ReactPy prepares to change `#!python number` to `#!python 1` on the next render.

Even though you called `#!python set_number(number + 1)` three times, in _this render's_ event handler `#!python number` is always `#!python 0`, so you set the state to `#!python 1` three times. This is why, after your event handler finishes, ReactPy re-renders the component with `#!python number` equal to `#!python 1` rather than `#!python 3`.

You can also visualize this by mentally substituting state variables with their values in your code. Since `#!python number` is `#!python 0` for _this render_, its event handler effectively reads:

```python linenums="0"
async def handle_click(event):
    set_number(0 + 1)
    set_number(0 + 1)
    set_number(0 + 1)
```

For the next render `#!python number` is `#!python 1`, so _that render's_ click handler reads `#!python set_number(1 + 1)` three times. This is why clicking again takes the counter to `#!python 2`, then `#!python 3`, and so on.

!!! info "This is Python's own closure rule, not a ReactPy feature"

    There is no magic here. `#!python handle_click` is a closure over the local name `#!python number` created during one specific call to `#!python counter()`. That name is bound to the value ReactPy handed to _that_ call, and no later assignment elsewhere can change what it refers to. ReactPy's contribution is simply that each render is a fresh call, so each render gets a fresh `#!python handle_click` closing over fresh values.

    It is worth stating plainly, because the usual Python instinct is wrong here: `#!python set_number` does **not** write to `#!python number`. It writes into ReactPy's hook state, on the shelf outside your function.

## State over time

Try to guess what this button's second column will show.

=== "app.py"

    ```python
    {% include "../../examples/state_as_a_snapshot/handler_sees_snapshot/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Using the substitution method, `#!python number` is `#!python 0`, so the first click records `#!python 0` — even though `#!python set_number(number + 5)` ran one line earlier. Click again and it records `#!python 5`, because in _that_ render `#!python number` is `#!python 5`.

But what if you delay that read, so it only happens _after_ the component re-renders? Would it say `#!python 0` or `#!python 5`? Have a guess!

=== "app.py"

    ```python
    {% include "../../examples/state_as_a_snapshot/delayed_handler/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Surprised? If you use the substitution method, you can see the "snapshot" of the state that was captured.

```python linenums="0"
set_number(0 + 5)
get_running_loop().call_later(3, delayed)   # delayed() closes over number == 0
```

The state stored in ReactPy may have changed by the time the callback runs, but the callback was scheduled using a snapshot of the state at the time the user interacted with it.

!!! warning "The updater form rescues only the value it updates"

    The scheduled callback above works because `#!python set_seen` is stable and the closure captures a value, not a live binding. The trap is the reverse: a callback that reaches for the *current* value gets the one from whichever render created it. An updater looks like the fix, but it is narrower than it appears. ReactPy applies an updater to the current value of **that one** state variable the instant you call the setter (`core/hooks.py`, `_CurrentState.dispatch` calls `new(self.value)`), so `#!python set_seen(lambda previous: [*previous, number])` hands you the freshest `#!python seen` — while `#!python number` inside it is still the name frozen when the callback was built. Reach for the updater when the value you need *is* the value you are setting. For anything else, read it before scheduling and pass it in, or keep it in a [`use_ref`](../reference/use-ref.md) box and read `#!python box.current` when the callback finally runs.

**A state variable's value never changes within a render,** even if its event handler's code is asynchronous. Inside _that render's_ `#!python handle_click`, the value of `#!python number` continues to be `#!python 0` even after `#!python set_number(number + 5)` was called. Its value was "fixed" when ReactPy "took the snapshot" of the UI by calling your component.

Here is an example of how that makes your event handlers less prone to timing mistakes. Below is a form that sends a message with a five-second delay. Imagine this scenario:

1. You press the "Send" button, sending "Hello" to Alice.
2. Before the five-second delay ends, you change the value of the "To" field to "Bob".

What do you expect the status line to display? Would it display, "You said Hello to Alice"? Or would it display, "You said Hello to Bob"? Make a guess based on what you know, and then try it:

=== "app.py"

    ```python
    {% include "../../examples/state_as_a_snapshot/delayed_message/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_as_a_snapshot/delayed_message/styles.css" %}
    ```

=== ":material-play: Run"

If you press Send and then change "To" before the five seconds elapse, you still get **"You said Hello to Alice"**. Verified: pressing Send and changing the recipient to `#!python "Bob"` mid-flight produced exactly that string.

That is the payoff of snapshots. `#!python handle_submit` was created by the render in which `#!python to` was `#!python "Alice"`, so it keeps saying `#!python "Alice"` no matter what later renders decide. Had the handler read the state through some live reference instead, changing the field mid-request would have sent the message to Alice while reporting that it went to Bob.

React's own version of this demo uses `setTimeout` and a browser `alert`. ReactPy has no `alert` on the server, so the equivalent here is a status paragraph — and `#!python asyncio.sleep` rather than a timer callback. If you want the browser to alert, that is the `#!python inlineJavaScript` escape hatch, not a Python function call.

## Recap

-   Setting state does not change the state variable you already have; it requests a render.
-   Every render captures its own snapshot of state, props, and handlers. Values are fixed for the duration of that render.
-   This follows Python's ordinary closure rules: each render is a fresh call, so each handler closes over fresh values.
-   Reading state inside a delayed callback or an `#!python await` gives you the value from the render that created that callback, which is usually what you want.
-   When you genuinely need the latest value inside a callback, use the updater form `#!python set_x(lambda previous: ...)`.
