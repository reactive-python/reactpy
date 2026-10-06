## Overview

<p class="intro" markdown>

Sometimes you need to do something a rendering model cannot express: focus an input, scroll an element into view, call a browser API ReactPy does not expose. In React you reach for a ref to hold the DOM node. ReactPy runs on the server and sends description-of-UI over a socket, so it has no DOM node to hand you — and the consequences shape everything on this page.

</p>

!!! summary "You will learn"

    -   Why there is no `<div ref={myRef}>` equivalent in ReactPy
    -   What happens if you pass a `#!python "ref"` attribute anyway
    -   How to focus, scroll, and restyle declaratively, and when you can't
    -   Why you must not mutate the DOM ReactPy renders

## There is no ref to the node

In React, you declare a ref, pass it to a tag, and React fills it in:

```python linenums="0"
# This is React, not ReactPy. It does not work.
<div ref={myRef}>
```

`#!python myRef.current` then holds a real DOM node you can call `#!python focus()` or `#!python scrollIntoView()` on. That works because React runs *in the browser*, next to the DOM.

ReactPy runs in your Python process. It builds a VDOM dictionary, serialises it to JSON, and sends it over a websocket; the browser-side client turns that JSON into DOM nodes. By the time a node exists, the code that described it has finished running, and there is no channel for the browser to send a node back. The "node" is on the other side of a network boundary.

### What `#!python "ref"` actually does

It is tempting to copy the React shape and put `#!python "ref"` in the attribute dict. Don't — both forms fail, and one of them fails quietly.

Passing a **dict** that looks like a ref is silently dropped:

```python linenums="0"
html.div({"ref": {"current": None}}, "...")
```

The key travels to the browser as an ordinary attribute. Even if the client writes a node into that object, it writes into its own throwaway copy decoded from the JSON — nothing can travel back up the socket into your Python dict. Measured: the element renders normally, `#!python as_dict["current"]` stays `#!python None` forever, and there is no error and no warning. A "focus the input" button built this way simply never focuses anything.

Passing a **string** is worse, because it throws in the browser:

```python linenums="0"
html.div({"ref": "my_ref"}, "...")
```

preact tries to assign to the string and the page dies with an uncaught:

```text
TypeError: Cannot create property 'current' on string 'my_ref'
```

The server logs nothing. Check the browser console.

## Focusing an input

If the input should be focused when it first appears, that is declarative — use the browser's own attribute and let ReactPy render it:

=== "app.py"

    ```python
    {% include "../../examples/manipulating_the_dom_with_refs/focus_on_mount/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

No ref, no effect, no JavaScript. The attribute dict is the DOM.

To focus *later*, in response to a click, there is no server-side way to reach a node — but ReactPy has an escape hatch for exactly this. When the value of an `#!python on*` key is a **string**, it runs as JavaScript in the browser (see [Responding to Events](./responding-to-events.md)). Give the element an `#!python "id"` and reach it by id:

=== "app.py"

    ```python
    {% include "../../examples/manipulating_the_dom_with_refs/focus_on_click/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This is the honest equivalent of `#!python myRef.current.focus()`. The trade-off is that the code doing the focusing now lives in a string, on the server, unchecked by your linter and invisible to your type checker. Keep it to one-line calls.

!!! warning "Re-rendering does not re-focus"

    A common wish is "re-fire `#!python autoFocus` when the user clicks again". Changing the element's `#!python "key"` really does remount it — ReactPy destroys and recreates the node, and a child's state resets — but `#!python autoFocus` does **not** re-trigger on that remount, because the browser only applies autofocus on initial page load. Measured: after re-keying, focus stayed on the button that was clicked. Use the inline-JS form above instead.

## Scrolling to an element

The React version of this example keeps three refs, one per image, and calls `#!python scrollIntoView()` on each. In ReactPy you give each item an id and let the browser find it:

=== "app.py"

    ```python
    {% include "../../examples/manipulating_the_dom_with_refs/scroll_to_item/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/manipulating_the_dom_with_refs/scroll_to_item/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/manipulating_the_dom_with_refs/scroll_to_item/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Note the f-string building the JavaScript: the id is interpolated server-side, so each button gets its own literal `#!python scrollIntoView` call. That is also the risk — the interpolation is not escaped. Interpolating anything a user controls into that string is an injection hole; interpolate your own integer keys, like `#!python person["id"]` above, and nothing else.

## Showing and hiding

Toggling visibility is the case where React's ref example and ReactPy agree on the *goal* but differ completely in method. There is no `#!python element.style.display = 'none'`; you render the difference:

=== "app.py"

    ```python
    {% include "../../examples/manipulating_the_dom_with_refs/toggle_visibility/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Pressing the button flips `#!python shown`, the `#!python "hidden"` attribute changes, and the client updates the element. Any style you would have set by hand goes in the attribute dict the same way — `#!python "style"` accepts a dict of camelCased CSS properties:

```python linenums="0"
html.div(
    {"style": {"color": "red", "fontSize": "20px", "fontWeight": "700"}},
    "styled text",
)
```

Changing a value in that dict from state re-renders the element with the new style, which is what you almost always want instead of touching `#!python element.style` from the browser.

## Two component-only features you cannot port

Two sections of React's version of this page have no ReactPy equivalent at all, and it is worth knowing they are absent rather than hunting for them:

-   **`useImperativeHandle`** / **`forwardRef`**. React lets a component expose a hand-picked slice of its DOM to a parent. There is no `#!python forward_ref` and no `#!python use_imperative_handle` in ReactPy — a component cannot hand a parent a node it does not have. If a parent must drive a child, pass a prop and let the child render it.
-   **`flushSync`**. React lets you force a synchronous repaint so that a subsequent DOM read sees the new values. ReactPy renders by sending a message, so there is nothing to flush; the client applies updates as they arrive.

## Best practices

Refs are an escape hatch, and here the hatch is even narrower: it is a string of JavaScript.

-   **Prefer declarative.** If the change can be expressed as an attribute, a class, a `#!python "style"` dict, a `#!python "key"`, or a conditional render, write that. It survives re-renders, and it is visible to your tools.
-   **Keep inline JavaScript to one call.** `#!python "document.getElementById('x').focus()"` is fine. A multi-statement script embedded in an attribute dict is unmaintainable and unlintable.
-   **Never interpolate user input into an inline-JS string.** Build the JS from your own constants and ids.
-   **Do not mutate DOM that ReactPy renders.** This is the same hazard as in React, and it is easier to hit because nothing warns you. If an inline-JS handler calls `#!python remove()` on an element ReactPy believes it owns, the next render that tries to update that element is working against a node that is gone. Toggle a state value and let ReactPy remove it.
-   **You may touch nodes ReactPy never manages.** An element ReactPy renders empty and never writes children to is yours to fill from inline JavaScript. It has no reason to update that subtree, so nothing conflicts.

## Summary

-   ReactPy is server-side: there is no DOM node to store in a ref, and `#!python {"ref": ...}` either vanishes (dict) or throws in the browser (string).
-   Express focus, visibility, and styling declaratively first: `#!python "autoFocus"`, `#!python "hidden"`, `#!python "style"`, conditional rendering.
-   For the imperative remainder — focus on click, scroll into view — give elements ids and use the inline-JavaScript handler form, keeping each snippet to a single call and interpolating only trusted values.
-   `#!python forwardRef`, `#!python useImperativeHandle`, and `#!python flushSync` do not exist in ReactPy.
-   Never mutate nodes ReactPy owns; remove them by changing state instead.
