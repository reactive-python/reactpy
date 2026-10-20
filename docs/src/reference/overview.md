<p class="intro" markdown>

This section is the detailed reference for ReactPy. For an introduction, start with the [Learn](../learn/quick-start.md) section.

</p>

The reference is split into functional subsections:

## Hooks

Call these at the top level of a component. ReactPy provides twelve:

-   [`use_state`](./use-state.md) — declare a state variable.
-   [`use_effect`](./use-effect.md) — run a synchronous side effect.
-   [`use_async_effect`](./use-async-effect.md) — run an `#!python async def` effect, or one that keeps running across renders.
-   [`use_reducer`](./use-reducer.md) — hold state behind a reducer.
-   [`use_context`](./use-context.md) — read a value provided higher in the tree.
-   [`use_ref`](./use-ref.md) — hold a mutable box that survives renders.
-   [`use_memo`](./use-memo.md) — cache a computed value.
-   [`use_callback`](./use-callback.md) — cache a function.
-   [`use_debug_value`](./use-debug-value.md) — attach a debug label to a component.
-   [`use_connection`](./use-connection.md) — inspect the current websocket connection.
-   [`use_scope`](./use-scope.md) — read the ASGI connection scope.
-   [`use_location`](./use-location.md) — read the browser's current URL.

There is no `use_id`, `use_transition`, `use_deferred_value`, `use_layout_effect`, `use_insertion_effect`, `use_imperative_handle`, or `use_sync_external_store`. Texts ported from React that rely on them have no ReactPy equivalent.

## HTML

How to describe markup. ReactPy has no JSX; you call functions.

-   [Common Props](./common-props.md) — attributes shared by every tag.
-   [Usage](./usage.md) — the `#!python html.*` functions and the shape of a VDOM dictionary.

## Executors

The ASGI applications that serve your components:

-   [ReactPy](./reactpy.md) — standalone single-page app; components render on the server.
-   [ReactPyMiddleware](./reactpy-middleware.md) — add ReactPy routes to an ASGI app you already have.
-   [ReactPyCsr](./reactpy-csr.md) — run component code in the browser via PyScript.

## Template integration

-   [Jinja](./jinja.md) — render components from Jinja templates.

## Rules of React

Idioms for expressing React patterns so they stay understandable and correct:

-   [Components and Hooks must be pure](./components-and-hooks-must-be-pure.md)
-   [React calls Components and Hooks](./react-calls-components-and-hooks.md)
-   [Rules of Hooks](./rules-of-hooks.md)

## Internals

-   [Protocol Structure](./protocol-structure.md) — the messages exchanged between server and client.
-   [Client API](./client-api.md) — the browser-side entry point.

## Where React differs

ReactPy models React's function-component API, but it is not React. Effects infer
their dependencies instead of requiring an array, state updates are replaced rather
than merged, an update that mutates in place is dropped without any error, and several
React hooks do not exist at all. Each page calls out the differences that matter to it,
so when porting code or prose from a React tutorial, read the ReactPy page rather than
assume parity.
