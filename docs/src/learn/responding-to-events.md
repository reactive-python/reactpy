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

    Note what does and does not decide "this is a handler". In `core/vdom.py`, `separate_attributes_handlers_and_inline_javascript` the test is **`callable(v)` on the value**, checked before the key is ever looked at: a callable under `#!python "on_click"`, or even under `#!python "foo"`, lands in `#!python eventHandlers`. That sort step is also where the coroutine requirement is enforced, because it builds an `#!python EventHandler` for the value — so any callable which cannot be awaited raises `#!python TypeError` at element-build time, whatever key it sits under. The key pattern `#!python ^on[A-Z]\w+` (`core/vdom.py`, `EVENT_ATTRIBUTE_PATTERN`) is used only for the *string* case below — it decides whether a string becomes `#!python inlineJavaScript` or a plain attribute. So `#!python {"onClick": "alert(1)"}` runs as JavaScript, while `#!python {"onclick": "alert(1)"}` and `#!python {"on_click": "alert(1)"}` become inert attributes.

An event handler has to be declared with `#!python async def`, so it cannot be written inline:

```python linenums="0"
async def handle_click(event):
    print("You clicked me!")


html.button({"onClick": handle_click}, "Click me")
```

!!! warning "A handler must be a coroutine — so a lambda never works"

    The first rule of an event handler is that it is declared `#!python async def`. ReactPy checks it the moment the element is built, and refuses anything else:

    ```text linenums="0"
    TypeError: handle_click cannot be used as an event handler because it is not a coroutine.
    Event handlers must be declared with 'async def':

        async def on_click(event):
            ...
    ```

    This is not ceremony. Reading the object an event fired from means waiting on the browser, and only a coroutine can await that round trip without stalling the layout — a blocking read would have to run off-loop, which is the one thread where `#!python set_state()` fails with `no running event loop`.

    The consequence for a `#!python lambda` is direct: a lambda can never be a coroutine, so `#!python {"onClick": lambda event: ...}` raises. Name the handler instead. Passing a state setter directly (`#!python {"onClick": set_count}`) is likewise refused — a setter is not a handler, and the `#!python TypeError` says so and shows you the fix.

    What *is* accepted: a plain `#!python async def`, a callable object whose `#!python __call__` is a coroutine, and a `#!python functools.partial` or `#!python functools.wraps` wrapper around either — `_unwrap_handler` in `core/events.py` peels partials and then runs `inspect.unwrap` before asking whether the result is a coroutine.

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

    In the second case the `#!python ()` calls `#!python handle_click` _immediately_ during [rendering](./render-and-commit.md), without any clicks — because the Python inside the call is evaluated right away, exactly like an expression inside JSX braces. Whatever it returns is what gets stored. Handlers are picked out by `#!python callable(v)`, so a `#!python None` return is not a handler: it falls through to the plain attributes and ships as `#!python {"onClick": None}`. The client never turns that into a DOM attribute — a value under an `on*` name is consumed as a listener, and a falsy one means "register nothing". Nothing fires, and the button renders and does nothing, forever.

    If `#!python handle_click` is a coroutine function — the only shape a handler may have — then calling it does not run its body at all; it returns a coroutine object. That is not `#!python callable` either, so it takes the same fall through to the attributes as `#!python None` does. The difference is what happens next: the layout renders, and the failure appears when the model is encoded for the wire — `TypeError: Type is not JSON serializable: coroutine` out of the `#!python orjson.dumps` on send (`executors/asgi/middleware.py`). So one form of this mistake gives you a silently dead button, the other a traceback at send time. Either way, pass the function; do not call it.

    The same trap appears with inline code:

    ```python linenums="0"
    # This prints when the component renders, not when clicked!
    html.button({"onClick": print("You clicked me!")}, "Click me")

    # Wrap it in a named coroutine so it becomes a function to call later.
    async def handle_click(event):
        print("You clicked me!")

    html.button({"onClick": handle_click}, "Click me")
    ```

    In both working cases, what you pass is a function. A `#!python lambda` cannot be the wrapper here, because a handler has to be `#!python async def`.

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

It is **not** React's `SyntheticEvent`, and it is not a serialized snapshot either. There is nothing to persist and no native object to unwrap: `#!python persist()` and `#!python nativeEvent` are React's answers to a pooling problem this design never had. They are not members of `#!python Event` — but `__getattr__` will happily hand you a proxy for either name, truthy and waiting to fail, so `#!python if event.persist:` and `#!python hasattr(event, "nativeEvent")` both say yes and only the `#!python await` raises `#!python EventProxyNotFound`. Never duck-type a proxy by attribute; read what you know is there. What your handler holds is a `#!python reactpy.types.Event` — a live, lazily resolved view onto the browser's object (`_event_proxy.py`, `Event`). Reading any property of it hands back another proxy, and *awaiting* the proxy is what asks the browser for the value:

```python linenums="0"
async def handle_change(event):
    value = await event.target.value   # one round trip
    await event.target.focus()         # methods are callable too
```

The property chain is spelled exactly as it is in JavaScript. The one difference is the `#!python await`, because the value lives in the browser rather than in this process. There is no dictionary behind it: `#!python event["target"]["value"]` raises `#!python TypeError: 'Event' object is not subscriptable`, because a proxy is deliberately not a container and has no `#!python __getitem__`, `#!python __iter__`, or `#!python __len__`.

Nothing is fetched until a handler asks for it, so a handler which only calls `#!python set_state()` never sends a request. Two things keep the count down for the handlers which do read. A property which has been read is remembered against its event, so reading it twice costs one trip. And properties which are in flight at the same moment go out as a single message:

```python linenums="0"
value, key = await event.read("target.value", "key")
value, key = await asyncio.gather(event.target.value, event.key)
```

Both cost one round trip. Two `#!python await` expressions written one after the other cannot be batched — the second is not known until the first has landed.

!!! warning "A read belongs to the moment it is awaited"

    `#!python await event.target.value` reports what the element holds **now**, just as the same expression would in JavaScript — not what it held when the keystroke fired. A handler still queued behind another event's work sees whatever that element has become by the time it runs. A handler which must act on the value as its own event saw it has to read it before anything else can change it.

    Reads are cached too, so a second read hands back what the first one found however much the page has moved on since. Ask the browser what it holds by now with `#!python refresh`:

    ```python linenums="0"
    (latest,) = await event.read("target.value", refresh=True)
    ```

Nothing is quietly answered with `#!python None`. A property the browser will not give — one it blocks, an object it has forgotten, a path that is not there — raises a subclass of `#!python EventProxyError` (`Unavailable`, `Timeout`, `NotFound`, `Evicted`, `AccessError`). A typo such as `#!python event.target.vallue` is therefore an error, not a silent `#!python None`. What *is* quiet is the mistake in the other direction: leave the `#!python await` off and you hold a proxy, which is always truthy and never raises on its own — it reaches `#!python set_state()` or an f-string as its own repr, or fails at the wire. A `#!python None` you did read is a real answer from the page: a property that exists and holds `#!python null` comes back as one.

The reads worth knowing:

| Read | Meaning |
| --- | --- |
| `#!python await event.target.value` | Text of an `#!html <input>`, `#!html <textarea>`, or selected `#!html <option>` |
| `#!python await event.target.checked` | Whether a checkbox or radio is on — read it from `#!python "onChange"`, which is the event that fires when one is toggled |
| `#!python await event.target.files` | Files from an `#!html <input type="file">` |
| `#!python await event.key` | Which key, on `#!python onKeyDown` / `#!python onKeyUp` |
| `#!python await event.type` | The event name, e.g. `#!python "click"` — the one value the client volunteers with the id, so awaiting it sends nothing |
| `#!python await event.target.dataset` | The element's `#!python data-*` attributes |
| `#!python await event.composedPath()` | The event's path, read from the browser |

Since the client holds the real object instead of serializing it, that list is a shortlist and not a ceiling. Anything the browser can answer is readable, and whatever it cannot turn into JSON — a DOM node, a `#!python DataTransfer` — comes back as a reference which is itself a proxy, so you can keep walking. What the client **refuses** is anything that could be used to break out of the page (`#!python window`, `#!python document`, `#!python parentNode`, `#!python __proto__`, `#!python eval`, ...) and anything that looks like an event handler, which is matched as `#!python /^on[a-z]/i` and so includes `#!python onPointerDown`. Whole-object views omit methods; an explicit method path still returns something callable.

!!! info "Form submits"

    For `#!python onSubmit` the target is the `#!html <form>` itself, which means `#!python value` is not there to read — `await event.target.value` raises `EventProxyNotFound`, and batching it into a `#!python read()` fails the whole read. A form does have a `#!python name`, so `#!python (name,) = await event.read("target.name")` works; to reach what was typed, ask for the control collection: `#!python controls = await event.target.elements`, then index `#!python c["value"]` on the entries it returns. See [Communicate Data Between Server and Client](./communicate-data-between-server-and-client.md#up-read-what-the-client-sends).

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

    Calling `#!python event.stopPropagation()` inside a handler does not itself stop anything: by the time your handler runs, the event has already bubbled. What stops propagation is a flag sent to the browser _in advance_, and ReactPy derives it by **inspecting the bytecode of your handler** (`core/_event_inspect.py`, `inspect_event_handler`).

    It looks for `#!python .stopPropagation` (and `#!python .preventDefault`, and `#!python .stopImmediatePropagation`) called directly on the **first parameter**. That produces some sharp edges, all of them observable:

    - The handler must take a parameter at all. `#!python async def handler():` can never be detected.
    - It must be the **first positional parameter**. Renaming it is fine; the position is what matters.
    - Rebinding defeats it. `#!python e = event` followed by `#!python e.stopPropagation()` is **not** detected, and propagation silently continues.
    - Passing the event into a helper that calls it is likewise not detected — the inspector reads one function's bytecode and does not follow calls.

    When in doubt, skip detection and declare the intent explicitly:

    ```python linenums="0"
    from reactpy import event

    @event(stop_propagation=True, prevent_default=True)
    async def handle_click(event): ...
    ```

    Because the live proxy keeps the browser object alive, the call is *also* forwarded to it without being waited for — but by then the browser has usually moved on, so rely on the handler flag when the action truly must not happen. `#!python event.propagationStopped` and `#!python event.defaultPrevented` answer synchronously, and with what **Python** asked for. What the browser settled on is a property like any other: `#!python (prevented,) = await event.read("defaultPrevented")`, which is worth the round trip when other scripts on the page may have prevented the action too.

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
    async def handle_toolbar_click(event):
        ...


    async def handle_play_click(event):
        ...


    html.div(
        {"onClickCapture": handle_toolbar_click},
        html.button({"onClick": handle_play_click}, "Play Movie"),
    )
    ```

    ReactPy forwards the key untouched — there is no capture logic in `#!js vdom.tsx` at all. The suffix is honoured one layer down, by Preact, which strips a trailing `#!python Capture`, registers the listener with `#!js addEventListener(name, handler, true)`, and dispatches `#!js "click"` to it in the capture phase. So `#!python "onClickCapture"` fires before the button's own `#!python "onClick"`, and the ordering is the browser's, not ReactPy's. Nothing in ReactPy checks that the name you gave is a real event, which is why the same freedom lets `#!python "onMyThing"` through and lets `#!python "on_click"` register a listener for `#!python "_click"` that nothing ever dispatches.

## Can event handlers have side effects?

Yes. Unlike component bodies, which must stay pure, event handlers run in response to an action rather than during rendering, so they are the correct place to change things. See [Where you _can_ cause side effects](./keeping-components-pure.md#where-you-can-cause-side-effects) for where side effects belong and why.

## Recap

-   Declare the handler with `#!python async def`. A `#!python def`, a `#!python lambda`, or a state setter is refused with a `#!python TypeError` when the element is built.
-   Add a handler by putting the **DOM event name in camelCase** into the attributes dictionary: `#!python {"onClick": handle_click}`.
-   Only names you define are `#!python snake_case`; `#!python "on_click"` renders but never fires.
-   Pass a function, never the result of calling one; a string value means client-side JavaScript, not Python.
-   Handlers may read props, call setters, and have side effects.
-   The event object is a **live proxy** onto the browser object, not a snapshot and not a `SyntheticEvent`. Read `#!python await event.target.value` and `#!python await event.key`; batch with `#!python await event.read("target.value", "key")`. Subscripting it raises.
-   Events bubble natively, with the browser's own exceptions such as `#!python "onScroll"`. Stop them with `#!python event.stopPropagation()`, which is detected from your bytecode — or declare it with `#!python @event(stop_propagation=True)`.
