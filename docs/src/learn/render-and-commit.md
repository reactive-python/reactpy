## Overview

<p class="intro" markdown>

Before your components are displayed on screen, they must be rendered by ReactPy. Understanding the steps in this process will help you think about how your code executes and explain its behavior.

</p>

!!! summary "You will learn"

    -   What rendering means in ReactPy
    -   When and why ReactPy renders a component
    -   The steps involved in displaying a component on screen
    -   Why rendering does not always produce a DOM update

A ReactPy component is a Python function that returns a description of the UI. That description has to travel from your server to someone else's browser before it becomes pixels. The journey has four steps:

1. **Triggering** a render — mounting the app, or updating state.
2. **Rendering** the component — Python calls your functions and builds a VDOM tree.
3. **Committing** to the DOM — the diff is sent over the websocket and patched into the page.
4. **Painting** — the browser redraws.

The first two happen in Python, on your server. The last two happen in the browser. Keeping that boundary in mind explains a lot of ReactPy's behavior that differs from a browser-only React app — most obviously the round-trip latency on every interaction.

## Step 1: Trigger a render

There are two reasons for a component to render:

1. It's the component's **initial render**, caused by mounting it.
2. The component's (or one of its ancestors') **state has been updated.**

### Initial render

When your app starts, you need to mount a root component. Unlike React, where you call `createRoot` yourself, in ReactPy the *executor* does the mounting, and which executor you pick determines what the mounting line looks like:

=== "app.py"

    ```python
    {% include "../../examples/render_and_commit/initial_render/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python ReactPy(image)` is the line that matters. It registers `#!python image` as the root component and, when a browser connects, calls it and sends the result down. There is no DOM node to hand in — the executor owns the mount point (`#!python <div id="app">` in the page it generates).

The other executors mount differently: `#!python ReactPyMiddleware` takes dotted paths to components so a URL can select one, and `#!python ReactPyCsr` mounts a component from a Python file that the browser runs itself. See [Creating a Standalone React App](./creating-a-react-app.md) for those.

### Re-renders when state updates

Once the component has been initially rendered, you can trigger further renders by updating its state with the `#!python set` function from `#!python use_state`. Updating your component's state automatically queues a render.

=== "app.py"

    ```python
    {% include "../../examples/render_and_commit/re_render/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Note the difference from a browser-only React app: the state lives on the server. Calling `#!python set_now(...)` schedules a render *on the server*, and the new VDOM reaches the browser a websocket message later. That is why an interaction in ReactPy feels slightly laggy compared to the same UI written in JavaScript, and why holding a lock or sleeping inside an event handler stalls the whole connection.

!!! info "Setting the same value does not re-render"

    Calling a setter with a value equal to the current one renders nothing — verified: `#!python set_n(0)` when `#!python n` is already `#!python 0` produces no further render at all, while `#!python set_n(n + 1)` does. Comparison is by identity, except that numbers, strings, and bytes compare by value (`core/hooks.py`, `strictly_equal`). Note this is a *state-update* bailout only; it is not component memoization — see step 2.

## Step 2: ReactPy renders your components

After you trigger a render, ReactPy calls your components to figure out what to display. **"Rendering" is ReactPy calling your functions.**

-   **On initial render,** ReactPy calls the root component.
-   **For subsequent renders,** ReactPy calls the function component whose state update triggered the render.

This process is recursive: if the updated component returns some other component, ReactPy renders _that_ component next, and if that component returns yet another, ReactPy renders that one too. In this way, a state update inside a component can trigger renders all the way down its children.

Under the hood, `Layout._render_component` compares the new component against the previous one at the same position. Two things matter here, and both are worth internalizing:

-   A component is matched by its **function object identity**. If you define a `#!python @component` inside another component, it is a brand-new function object on every render, so ReactPy unmounts the old one and loses all its state. Always define components at module level.
-   Children are matched by `#!python key`, falling back to position. See [Keeping list items in order with `key`](./rendering-lists.md#keeping-list-items-in-order-with-key).

!!! warning "Every child re-renders; there is no memo"

    ReactPy has no component-level `#!python memo`. A child function runs again whenever its parent renders, even when its props are identical — verified by instrumenting a sibling: it re-ran on the parent's state update. `#!python use_memo` caches *values* inside a component, not whole component subtrees.

    This makes the "don't nest component definitions" rule above more than a style preference, and it means expensive children stay expensive. If a subtree is genuinely costly, the tools are `#!python use_memo` for the computation and moving state down so fewer components re-render — not wrapping the child.

!!! warning "ReactPy will not render twice to catch you"

    React's Strict Mode double-invokes components in development to expose impure rendering. **ReactPy has no Strict Mode and never double-invokes.** A component that mutates module state or reads the clock will render perfectly once and misbehave later. If you want that safety net, write the test: render the component twice inside a `reactpy.core.layout.Layout` and assert the two results are equal.

## Step 3: Commit to the DOM

After a component renders, ReactPy has a Python description of the UI. This is **not** yet on the screen — ReactPy must deliver it to the browser, which must then update the DOM:

1. **Update the DOM.** ReactPy's client applies the changes to existing DOM nodes, patching rather than replacing wherever it can.
2. **Display the DOM.** The browser updates the screen to reflect the changes.

The first half happens on the server: ReactPy walks the new tree, computes a diff, and sends it over the websocket as a `path` plus a partial model. The second half happens in the browser, where the bundled client patches that subtree in place.

This is where ReactPy is most different from React, and it's the most useful thing to understand. React re-renders from the root and diffs the whole tree; **ReactPy sends a patch addressed to one path in the tree.** Observed directly: after clicking a button inside the first of two children, the update carried the path `#!python "/children/0/children/0"` and a model describing only that button's subtree. Nothing about the untouched sibling went over the wire.

Because the patch is applied to existing nodes rather than rebuilt, DOM state that ReactPy doesn't know about survives. Verified in a browser: an `#!html <input>` with no `#!python value` attribute kept both its typed text **and** its focus across a parent re-render, and was the *same node object* before and after.

That is the practical payoff of the "controlled vs uncontrolled" distinction:

=== "app.py"

    ```python
    {% include "../../examples/render_and_commit/uncontrolled_input/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Type into the field, then click **Re-render**. The text stays. ReactPy re-runs `#!python app()`, produces a new tree, and the diff for the untouched input is empty — so the browser never touches it, and neither the user's text nor their cursor position is disturbed.

Had that input carried `#!python "value": something`, ReactPy would own it and rewrite it on every render, which is what you want when the value is genuinely derived from state — and what makes typing feel broken when you forget the matching `#!python onChange`.

!!! info "You can skip the browser entirely"

    Because rendering is pure Python, the same components can be rendered to an HTML string with `#!python reactpy_to_string` from `reactpy.utils` — no browser, no websocket. This is how server-side rendering works in ReactPy, and it is only safe because rendering is pure. A component that reads the clock or mutates a global will leak one request's output into another's.

## Epilogue: Browser paint

After ReactPy has patched the DOM, the browser repaints the screen. Although this process is known as "browser rendering", we'll refer to it as "painting" to avoid confusion throughout the docs.

Because a round trip sits between the click and the paint, ReactPy apps feel more like a networked app than a local one. Two habits follow from that: keep event handlers short (they run on the server, blocking that connection), and prefer optimistic UI where a wrong guess is cheap.

## Recap

-   Any screen update in a ReactPy app happens in four steps:
    1. Trigger
    2. Render (Python, on the server)
    3. Commit (a path-addressed patch over the websocket)
    4. Paint (the browser)
-   Mounting a root component triggers the initial render; the executor decides how.
-   Setting state queues a render; setting it to an equal value queues nothing.
-   Children always re-run — there is no `memo`, so keep definitions at module level and expensive work in `use_memo`.
-   ReactPy has no Strict Mode, so nothing will double-render your components to expose impurity for you.
-   Untouched parts of the tree are neither recomputed for the wire nor rewritten in the DOM, which is why an uncontrolled input keeps what the user typed.
