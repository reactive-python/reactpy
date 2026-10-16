## Overview

<p class="intro" markdown>

ReactPy lets you add _event handlers_ to your VDOM. Event handlers are your own functions that will be triggered in response to interactions like clicking, hovering, focusing form inputs, and so on.

</p>

!!! summary "You will learn"

    -   Different ways to write an event handler
    -   How to pass event handling logic from a parent component
    -   How events propagate and how to stop them
    -   What the event object actually contains

## Adding event handlers

To add an event handler, you first define a function and then [pass it as a prop](./passing-props-to-a-component.md) to the appropriate tag. For example, here is a button that doesn't do anything yet:

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/simple_button.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

You can make it show a message when a user clicks by following these three steps:

1. Declare a function called `#!python handle_click` _inside_ your `#!python def button()` component.
2. Implement the logic inside that function (use `#!python print` to show the message).
3. Add `#!python "onClick": handle_click` to the `#!python html.button` attributes dictionary.

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/simple_button_event.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/responding_to_events/simple_button_event.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

You defined the `#!python handle_click` function and then [passed it as a prop](./passing-props-to-a-component.md) to `#!python html.button`. `#!python handle_click` is an **event handler.** Event handler functions:

-   Are usually defined _inside_ your components.
-   Have names that start with `#!python handle`, followed by the name of the event.

By convention, it is common to name event handlers as `#!python handle` followed by the event name. You'll often see `#!python "onKeyDown": handle_key_down`, `#!python "onMouseEnter": handle_mouse_enter`, and so on.

!!! warning "The handler key is camelCase, and it lives in the attributes dict"

    This is the single most common mistake when moving from ReactJS examples. The key is the **DOM event name in camelCase** — `#!python "onClick"`, `#!python "onChange"`, `#!python "onSubmit"` — and it goes **inside the attributes dictionary**, not as a keyword argument:

    ```python linenums="0"
    html.button({"onClick": handle_click}, "Click me")   # correct
    ```

    Writing `#!python html.button({"on_click": handle_click}, ...)` does **not** raise. ReactPy ships it to the browser verbatim as a handler for an event called `#!python _click` — the client registers a listener for the key with the leading `#!js on` stripped — and no browser ever fires one. The button looks fine and simply never responds. Only the names *you* define (variables, components, component props) are `#!python snake_case`.

    Note what does and does not decide "this is a handler". In `core/vdom.py`, `separate_attributes_handlers_and_inline_javascript` the test is **`callable(v)` on the value**, checked before the key is ever looked at: a callable under `#!python "on_click"`, or even under `#!python "foo"`, lands in `#!python eventHandlers`. The key pattern `#!python ^on[A-Z]\w+` (`core/vdom.py`, `EVENT_ATTRIBUTE_PATTERN`) is used only for the *string* case below — it decides whether a string becomes `#!python inlineJavaScript` or a plain attribute. So `#!python {"onClick": "alert(1)"}` runs as JavaScript, while `#!python {"onclick": "alert(1)"}` and `#!python {"on_click": "alert(1)"}` become inert attributes.

Alternatively, you can define an event handler inline with a `#!python lambda`:

```python linenums="0"
html.button(
    {"onClick": lambda event: print("You clicked me!")},
    "Click me",
)
```

Inline event handlers are convenient for short functions.

!!! warning "A string is not a handler — it is JavaScript"

    ReactPy has a second, easy-to-miss form. If the value of an `#!python on*` key is a **string**, ReactPy treats it as JavaScript to run in the browser instead of calling your Python code:

    ```python linenums="0"
    html.button({"onClick": "alert('You clicked me!')"}, "Click me")
    ```

    That renders into an `#!python inlineJavaScript` field on the VDOM node rather than an `#!python eventHandlers` field, and nothing on the server ever runs. It is a real escape hatch for things only the browser can do, but it is never what you want when you meant to write a Python function. If your handler silently does nothing, check whether you passed a string.

!!! warning "Pass the function, don't call it"

    Functions passed to event handlers must be passed, not called:

    ```python linenums="0"
    html.button({"onClick": handle_click}, "...")    # correct: fires on click
    html.button({"onClick": handle_click()}, "...")  # wrong: fires during render
    ```

    In the second case the `#!python ()` calls `#!python handle_click` _immediately_ during [rendering](./render-and-commit.md), without any clicks — because the Python inside the call is evaluated right away, exactly like an expression inside JSX braces. Whatever it returns is what gets stored, and a function that ends without a `#!python return` gives `#!python None`. ReactPy does not reject that: handlers are picked out by `#!python callable(v)`, and `#!python None` is not callable, so it falls through to the plain attributes and ships as `#!python {"onClick": None}` — a DOM attribute named `onClick` holding `null`. Nothing registers, nothing fires, and the button renders and does nothing, forever.

    The same trap appears with inline code:

    ```python linenums="0"
    # This prints when the component renders, not when clicked!
    html.button({"onClick": print("You clicked me!")}, "Click me")

    # Wrap it in a lambda so it becomes a function to call later.
    html.button({"onClick": lambda event: print("You clicked me!")}, "Click me")
    ```

    In both working cases, what you pass is a function.

### Reading props in event handlers

Because event handlers are declared inside a component, they have access to the component's props. Here is a button that, when clicked, displays its `#!python message` prop:

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/reading_props/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This lets the two buttons show different messages. Try changing the messages passed to them.

Note the `#!python set_shown(message)` line: the handler closes over the `#!python message` **prop**, which is a plain function parameter, so this behaves like any other Python closure.

### Passing event handlers as props

Often you'll want the parent component to specify a child's event handler. Consider buttons: depending on where you're using a `#!python button()` component, you might want to execute a different function—perhaps one plays a movie and another uploads an image.

To do this, pass a prop the component receives from its parent as the event handler:

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/handler_props/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Here, `#!python toolbar()` renders a `#!python play_button()` and an `#!python upload_button()`:

-   `#!python play_button()` passes `#!python handle_play_click` as the `#!python on_click` prop to the `#!python button()` inside.
-   `#!python upload_button()` passes `#!python handle_upload_click` as the `#!python on_click` prop.

Finally, the `#!python button()` component accepts a prop called `#!python on_click` and passes it straight to the built-in browser button with `#!python {"onClick": on_click}`. This tells ReactPy to call the passed function on click.

Notice the two levels of naming: the prop your own component accepts is an ordinary Python parameter (`#!python on_click`, snake_case), while the key handed to the browser tag is `#!python "onClick"`. A [design system](https://uxdesign.cc/everything-you-need-to-know-about-design-systems-54b109851969) commonly puts styling in components like buttons but leaves the behavior to callers, so `#!python play_button()` and `#!python upload_button()` pass handlers down.

### Naming event handler props

Built-in tags like `#!python html.button` and `#!python html.div` only support [DOM event names](https://developer.mozilla.org/en-US/docs/Web/Events) as handler keys — `#!python "onClick"`, `#!python "onChange"`, and so on. When you build your own components, however, you can name their handler props anything you like, because they are just Python parameters.

By convention, name them `#!python on_` followed by the interaction:

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/naming_props/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

In this example `#!python {"onClick": on_smash}` shows that the browser button still needs the key `#!python "onClick"`, but the prop name received by your own `#!python button()` component is up to you.

When a component supports multiple interactions, name handler props after app-specific concepts. A `#!python toolbar()` could receive `#!python on_play_movie` and `#!python on_upload_image`. The calling `#!python app()` does not need to know _what_ `#!python toolbar()` will do with them — that's an implementation detail. It could wire them to a click today and a keyboard shortcut tomorrow. Naming props after app-specific interactions gives you that flexibility.

!!! info "Use the right tag"

    Use the semantically correct HTML tag for the interaction. To handle clicks, use `#!python html.button({"onClick": handle_click})` rather than `#!python html.div({"onClick": handle_click})`. A real browser `#!python <button>` gives you built-in behavior such as keyboard navigation and focus handling. If you dislike the default styling, restyle it with CSS rather than downgrading it to a `#!html <div>`. [Learn more about writing accessible markup.](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML)

## The event object

Handlers receive the event data as their **single positional argument**. By convention it's called `#!python event`.

It is **not** React's `SyntheticEvent`. There is no `#!python nativeEvent`, no `#!python persist()`, no event pooling. It is JSON that the browser sent over the websocket, wrapped in `#!python reactpy.types.Event` — a `#!python dict` subclass that adds attribute access into nested dictionaries:

```python linenums="0"
def handle_change(event):
    event["target"]["value"]   # dictionary style
    event.target.value         # identical, attribute style
```

Both forms are equivalent, and each step down re-wraps the nested dictionary so chaining works. But a missing key reads as `#!python None` instead of raising, so a typo such as `#!python event.target.vallue` fails silently. Reach for `#!python event.get("target", {})` when a missing value should be a real error.

The properties that reliably arrive are those the client deliberately keeps:

| Read | Meaning |
| --- | --- |
| `#!python event["target"]["value"]` | Text of an `#!html <input>`, `#!html <textarea>`, or selected `#!html <option>` |
| `#!python event["target"]["checked"]` | Whether a checkbox or radio is on (use `#!python "onChange"`, which the client maps to `#!python input` for checkboxes) |
| `#!python event["target"]["files"]` | Files from an `#!html <input type="file">` |
| `#!python event["key"]` | Which key, on `#!python onKeyDown` / `#!python onKeyUp` |
| `#!python event["type"]` | The event name, e.g. `#!python "click"` |
| `#!python event["target"]["dataset"]` | The element's `#!python data-*` attributes |
| `#!python event["target"][name]` | On `#!python onSubmit`, each named control of the form |

ReactPy's client serializes the DOM event's own enumerable properties, plus the five highlighted ones (`#!python value`, `#!python checked`, `#!python files`, `#!python type`, `#!python name`) which it re-reads directly from the element so they survive even when the element hides them, and the current text selection.

It **drops** methods, anything `#!python __`-prefixed or all-caps, and — to avoid enormous payloads and layout thrash — a long denylist of element properties including `#!python innerHTML`, `#!python outerHTML`, `#!python childNodes`, `#!python parentNode`, `#!python offsetWidth`, and `#!python scrollTop`. So `#!python event.target.parentNode` is simply not there, and neither is anything that would need the real DOM node.

!!! info "Form submits hand you the named fields"

    For `#!python onSubmit` the target is the `#!html <form>` itself, and each control that has a `#!python name` is flattened onto it. That makes it easy to read a whole form without a `#!python use_state` per field.

## Event propagation

Event handlers also catch events from any children a component has. We say that an event "bubbles" or "propagates" up the tree: it starts where the event happened, and then goes up.

ReactPy attaches an ordinary DOM listener to each element, so bubbling is the **browser's** native behavior rather than something ReactPy implements. That has one consequence worth knowing: unlike React, which delegates every event to the document root and then replays it down your component tree, ReactPy's handlers follow the real DOM tree. A parent handler fires for events from anything nested inside it, including elements you did not render yourself.

This `#!html <div>` contains a button. Both the `#!html <div>` _and_ the button have their own `#!python "onClick"` handlers. Which do you think fire when you click the button?

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/propagation/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/responding_to_events/propagation/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

If you click the button, its `#!python "onClick"` runs first, followed by the parent `#!html <div>`'s. Two messages appear. If you click the toolbar itself, only the parent's handler runs.

!!! warning "Scroll does not bubble"

    Because propagation is the browser's own, the browser's exceptions apply. `#!python "onScroll"` does not bubble: attaching it to an ancestor will not catch scrolls from descendants. Attach it to the element that actually scrolls.

### Stopping propagation

To prevent an event from reaching parent components, call `#!python event.stopPropagation()`:

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/stop_propagation/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/responding_to_events/stop_propagation/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Now clicking the button produces only `"Playing!"`.

!!! warning "ReactPy detects this call by reading your bytecode"

    `#!python event.stopPropagation()` is a no-op on the server — by the time your handler runs, the browser event is long gone. What actually stops propagation is a flag sent to the browser _in advance_, and ReactPy derives it by **inspecting the bytecode of your handler** (`core/_event_inspect.py`, `inspect_event_handler`).

    It looks for `#!python .stopPropagation` (and `#!python .preventDefault`) accessed directly on the **first parameter**. That produces some sharp edges, all of them observable:

    - The handler must take a parameter at all. `#!python def handler():` can never be detected.
    - It must be the **first positional parameter**. Renaming it is fine; the position is what matters.
    - Rebinding defeats it. `#!python e = event` followed by `#!python e.stopPropagation()` is **not** detected, and propagation silently continues.
    - Passing the event into a helper that calls it is likewise not detected.

    When in doubt, skip detection and declare the intent explicitly:

    ```python linenums="0"
    from reactpy import event

    @event(stop_propagation=True, prevent_default=True)
    async def handle_click(event): ...
    ```

### Preventing default behavior

Call `#!python event.preventDefault()` the same way to stop the browser's built-in action. The classic case is a form submit, which would otherwise navigate away from the page:

=== "app.py"

    ```python
    {% include "../../examples/responding_to_events/prevent_default/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The same detection rules — and the same `#!python @event(prevent_default=True)` escape hatch — apply.

!!! info "Capture-phase handlers"

    To see an event on the way _down_, before your children handle it, append `#!python Capture` to the event name:

    ```python linenums="0"
    html.div(
        {"onClickCapture": handle_toolbar_click},
        html.button({"onClick": handle_play_click}, "Play Movie"),
    )
    ```

    ReactPy forwards the key untouched, and the client registers it with `#!python addEventListener("click", handler, True)`, so `#!python "onClickCapture"` fires before the button's own `#!python "onClick"`. This works because it maps onto a real DOM capability rather than a React invention — which also means the ordering is the browser's, not ReactPy's.

## Can event handlers have side effects?

Yes. Unlike component bodies, which must stay pure, event handlers run in response to an action rather than during rendering, so they are the correct place to change things. See [Where you _can_ cause side effects](./keeping-components-pure.md#where-you-can-cause-side-effects) for where side effects belong and why.

## Recap

-   Add a handler by putting the **DOM event name in camelCase** into the attributes dictionary: `#!python {"onClick": handle_click}`.
-   Only names you define are `#!python snake_case`; `#!python "on_click"` renders but never fires.
-   Pass a function, never the result of calling one; a string value means client-side JavaScript, not Python.
-   Handlers may read props, call setters, and have side effects.
-   The event object is a `#!python dict`-subclass snapshot of browser data, not a `SyntheticEvent`; read `#!python event["target"]["value"]`, `#!python event["key"]`, and friends, and don't expect DOM-node properties.
-   Events bubble natively, with the browser's own exceptions such as `#!python "onScroll"`. Stop them with `#!python event.stopPropagation()`, which is detected from your bytecode — or declare it with `#!python @event(stop_propagation=True)`.
