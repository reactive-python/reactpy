# ReactPy v2.0.0 — Agent Context

Compact reference for writing/reviewing ReactPy v2 docs. Every claim verified against
`reactive-python/reactpy@main` (`aafabc2965`, `reactpy==2.0.0b13`) or this repo's
`docs/examples/`. Cites are `file:line` on `main`.

Rules for docs work: snake_case everywhere, never invent an API, keep Python runnable,
verify a claim in source/tests before writing it.

---

## 1. Public surface

`src/reactpy/__init__.py` — everything below is importable as `from reactpy import X`:

```python
from reactpy import (
    component, create_context, event, h, html, hooks, use_async_effect,
    use_callback, use_connection, use_context, use_debug_value, use_effect,
    use_location, use_memo, use_reducer, use_ref, use_scope, use_state,
    widgets, types, config, logging, reactjs, web,
    Ref, Vdom, reactpy_to_string, string_to_reactpy, pyscript_component,
)
```

Prefer `from reactpy import component, html` (matches every file in `docs/examples/`).
`reactpy.hooks` and `reactpy.utils` submodules are also reachable (`reactpy.hooks.use_state`,
`reactpy.utils.Ref`). `h` is a documented alias of `html` (`_html.py`, `h = html  # shorthand alias for html`).

**Hooks that exist (all 13):** `use_state`, `use_effect`, `use_async_effect`,
`use_reducer`, `use_context`, `use_ref`, `use_memo`, `use_callback`, `use_debug_value`,
`use_connection`, `use_scope`, `use_location` + `create_context`.

**Hooks that DO NOT exist** (ReactJS-only — never show them as ReactPy):
`useTransition`, `useDeferredValue`, `useId`, `useLayoutEffect`, `useImperativeHandle`,
`useInsertionEffect`, `useSyncExternalStore`, `useOptimistic`, `useActionState`.
Their `docs/src/reference/use-*.md` pages are ReactJS copies already stamped
`!!! warning "Planned / Undeveloped"`.

## 2. Components

```python
@component
def my_button():
    return html.button("I'm a button!")
```

- `component(function)` is a plain decorator; no options
  (`core/component.py`).
- **Naming is snake_case and lowercase.** The ReactJS "must start with a capital
  letter" rule does NOT apply — ReactPy distinguishes components from tags by call,
  not by case. Docs use `my_button`, `filterable_product_table`, `search_bar`.
- Returns `Component | VdomDict | str | None` (`core/component.py`).
- `key` is a **reserved parameter**: a component may not declare a `key` argument.
  `TypeError: Component render function ... uses reserved parameter 'key'`
  (`core/component.py`).
- Call a child component with `key=` as a keyword: `Item(item_id, key=item_id)`
  (`test_events.py`, `test_event_targeting_with_shifting_elements`).
- Props = normal Python parameters (positional and/or keyword). No JSX children.
- Async components are not a documented feature of v2.0.0b13. Do not claim them.

## 3. HTML / VDOM

Tags are **attributes on the `html` object**, resolved by `__getattr__`
(`_html.py`, `HtmlConstructor.__getattr__`). Two call forms (`core/vdom.py`, `Vdom.__call__`):

```python
html.button("Click Me")                                  # children only
html.button({"onClick": on_click, "id": "click"}, "Click Me!")  # dict first, then children
```

- The **first positional arg is the attribute dict only if it is exactly a `dict`**
  (`vdom.py: type(values[0]) is dict`). Otherwise every positional arg is a child.
- `class_name` does NOT exist. Use the DOM/React name: `{"className": "avatar"}`
  (`docs/examples/quick_start/adding_styles.py:4`). Attribute keys are passed through
  verbatim to the client; there is no snake_case→camelCase conversion for attributes.
- `style` is a dict of camelCase CSS properties: `{"style": {"color": "red"}}`.
- **`key` is spelled two different ways depending on what you are creating**, and mixing
  them up is a hard error. For an *element* it goes in the attribute dict
  (`html.li({"key": 1}, ...)`); passing it as a keyword raises
  `TypeError: Vdom.__call__() got an unexpected keyword argument 'key'`. For a *component*
  it is the keyword (`my_row(item, key=1)`); putting it in a dict is meaningless there.
  Verified in a real browser round-trip, not just by reading source.
- Dashed/illegal Python names: trailing `_` is stripped, `_` becomes `-`.
  `html.del_` → `<del>`, `html.data_table` → `<data-table>` (`_html.py`, `HtmlConstructor.__getattr__`).
- Fragments: `html()` or `html.fragment(...)`. Accepts **only** a `key` attribute;
  anything else → `TypeError: Fragments cannot have attributes besides 'key'`
  (`_html.py`, `_fragment`; `tests/test_html.py`, `test_fragment_can_have_no_attributes`).
- SVG is a nested constructor: `html.svg({"width": 100}, html.svg.circle({"r": 40}))`
  (`tests/test_html.py`, `test_svg`).
- Void tags (`img`, `input`, `br`, `hr`, `link`, `meta`, `iframe`, ...) reject children:
  `TypeError: 'img' nodes cannot have children.` (`_html.py`, `NO_CHILDREN_ALLOWED_HTML_BODY`; `core/vdom.py`, `Vdom.__call__`).
- `html.script` is special: at most one child, must be a string, no event handlers
  (`_html.py`, `_script`; `tests/test_html.py`, `test_script_may_only_have_one_child`).
- Children are flattened one level deep for any non-str/non-Mapping iterable
  (`vdom.py: _flatten_children`). `None` is skipped by the layout
  (`layout.py: _get_children_info`).
- Debug-mode key lint: a `Component` or element child in a list without a key warns
  `Key not specified for child in list ...` (`vdom.py: _validate_child_key_integrity`),
  active under `REACTPY_DEBUG`. Passing a generator (no `__len__`) warns
  `Did not verify key-path integrity of children in generator ...` — pass a `list`.

## 4. Events

Event keys are **camelCase DOM names** (`onClick`, `onChange`, `onKeyDown`) — the same
keys ReactJS uses (`tests/test_html.py`, `tests/test_core/test_events.py` — every handler in both uses `onClick`/`onChange`/`onKeyDown`).

```python
def handle_click(event):
    print("You clicked me!")

html.button({"onClick": handle_click}, "Click me")   # docs/examples/responding_to_events/simple_button_event.py
```

- Handlers may be sync `def`, `async def`, or a `lambda`. ReactPy wraps them
  (`events.py: to_event_handler_function`).
- The handler receives the **event payload as a single positional arg** — client data is
  a list, unpacked positionally onto the handler's parameters
  (`core/events.py`, `to_event_handler_function`; `tests/test_core/test_events.py`,
  `test_to_event_handler_function` → `([1, 2, 3])` yields `args == (1, 2, 3)`). Name it `event`.
- The value is a `reactpy.types.Event` — a `dict` subclass with **attribute access into
  nested dicts** (`types.py: Event.__getattr__`):

  ```python
  event["target"]["value"]      # dict style
  event.target.value            # identical, attribute style
  ```
- Supported payload reads, **verified in a real headless Chrome round-trip** (not just by
  reading the serializer): `event["target"]["value"]`, `event["target"]["checked"]`,
  `event["key"]`, `event["type"]`, `event["target"]["dataset"]`.
  `checked` **works** — a checkbox `onChange` handler receives `checked=True`. The
  `FIXME: ... event["target"]["checked"] doesn't exist` comment in
  `docs/src/learn/thinking-in-react.md` is **wrong** and should be removed when that page is
  touched: the client serializer deliberately re-reads `["value","checked","files","type",
  "name"]` off the element via `prop in x` (`static/index.js`, the `classToObject` helper),
  which bypasses enumerability entirely. Do not repeat the FIXME's claim.
- **Capture-phase handlers work.** Append `Capture` to the key (`{"onClickCapture": h}`);
  ReactPy forwards it untouched and the client strips the suffix and registers with
  `addEventListener(type, handler, true)`. Verified order: capture parent → child → bubble
  parent. Do not write that ReactPy lacks capture support.
- `onScroll` does **not** bubble (native DOM behavior): a parent `onScroll` does not fire for
  a descendant's scroll. Since ReactPy attaches real DOM listeners rather than delegating at
  the document root like React, the browser's own exceptions apply — verify before claiming
  any propagation behavior.
- A handler key that is not a real DOM event (`{"on_click": h}`) and a handler that is `None`
  (from accidentally calling the function) both **render without error and never fire**.
  Confirmed in-browser: neither produced a single server-side invocation.
- `event.preventDefault()`, `event.stopPropagation()`, and assigning
  `event.debounce = <ms>` are detected by **bytecode inspection** of the handler:
  `prevent_default` / `stop_propagation` / `debounce` get set automatically
  (`core/events.py`, `EventHandler.__init__`; `tests/test_core/test_events.py`,
  `test_detect_prevent_default`, `test_detect_stop_propagation`, `test_detect_debounce`). Detection fails for a
  computed value (`event.debounce = get_debounce()` → stays `None`,
  `test_computed_debounce_value_is_not_detected`).
- `@event(...)` decorator adds the same controls explicitly
  (`core/events.py`, `event`):

  ```python
  @event(prevent_default=True)
  async def on_key_down(value): ...
  ```
  kwargs: `stop_propagation`, `prevent_default`, `debounce` (server→client value
  updates on inputs), `throttle` (client→server outgoing rate limit).
- Inline JS handlers are supported: a `str` value on an `onXxx` key becomes client JS —
  `{"onClick": '(e) => e.target.innerText = "Thank you!"'}` or
  `{"onClick": "this.innerText = ..."}` (`vdom.py: EVENT_ATTRIBUTE_PATTERN`;
  `test_events.py: test_javascript_event_as_arrow_function`).
- Controlled input idiom (verified end-to-end):

  ```python
  value, set_value = use_state("")

  def on_change(event):
      set_value(event.target.value)

  html.input({"value": value, "onChange": on_change})
  ```
  Inputs are debounced client-side by default (200 ms); the server value is reconciled
  once the window expires (`types.py: BaseEventHandler.debounce`;
  `test_controlled_input_default_debounce_reconciles_server_value`).

## 5. Hooks

All signatures from `core/hooks.py`. **Every `dependencies` argument is `...`-by-default,
NOT `None`-by-default**, and it is **inferred from the closure** when omitted.

```python
use_state(initial_value)                                    -> State[value, set_value]
use_effect(function=None, dependencies=...)                 -> decorator | None
use_async_effect(function=None, dependencies=..., shield=False)
use_reducer(reducer, initial_value)                         -> (state, dispatch)
create_context(default_value)                               -> Context
use_context(context)                                        -> value
use_connection()                                            -> Connection
use_scope()                                                 -> scope dict
use_location()                                              -> Location(path, query_string)
use_callback(function=None, dependencies=...)
use_memo(function=None, dependencies=...)
use_ref(initial_value)                                      -> Ref
use_debug_value(message, dependencies=...)
```

- **`use_state` returns a `State` NamedTuple** `(value, set_value)` (`types.py`, `State`).
  Unpack as `count, set_count = use_state(0)`.
- `initial_value` may be a **callable of no args** used as a lazy constructor
  (`core/hooks.py`, `use_state`). Unlike ReactJS this is resolved once and stored, so it is not
  re-created per render.
- **The setter DOES accept an updater function**: `set_count(lambda prev: prev + 1)`
  (`core/hooks.py`, `_CurrentState.dispatch`). A new value that is *strictly equal*
  to the current one **skips the re-render**.
- Deps use **identity**, not ReactJS `Object.is` on arrays: `strictly_equal()` compares by
  `id()` except for `int/float/complex/str/bytes/bytearray/memoryview`, which compare by
  `==` (`hooks.py: strictly_equal`). Lambdas/local functions are compared by **bytecode
  source**, so an identical inline lambda across renders does not retrigger an effect.
- `use_effect` **rejects `async def`**:
  `TypeError: use_effect does not support async functions. Use use_async_effect instead.`
  (`core/hooks.py`, `use_effect.decorator`).
- Effects return a **cleanup function** (or `None`); it runs before the next effect and on
  unmount (`core/hooks.py`, `use_effect`). With `use_async_effect` the effect body runs as an
  `asyncio.Task` that is **cancelled** when deps change or on unmount unless
  `shield=True` (`core/hooks.py`, `use_async_effect`).
- `use_async_effect` takes a **zero-argument** coroutine: it calls `func()` with no `stop`
  event (`core/hooks.py`, `use_async_effect.decorator` -> `asyncio.create_task(func())`).
  The `async def effect(stop)` signature carried over from ReactPy 1.x raises
  `TypeError: ... missing 1 required positional argument: 'stop'`. Loop on `while True:` and
  let cancellation end it, or return a cleanup function.
- Effects run **after the layout renders** (`affect_layout_did_render`,
  `core/_life_cycle_hook.py`, `affect_layout_did_render`) — same ordering guarantee as ReactJS.
- Hooks are positional-indexed per component (`_life_cycle_hook.py: LifeCycleHook.use_state`):
  calling a hook inside a branch/loop silently shifts state to the wrong slot. There is
  **no guard and no warning** for conditional hooks — the only error is
  `RuntimeError: No life cycle hook is active. Are you rendering in a layout?`
  (`core/_life_cycle_hook.py`, `_HookStack.current_hook`) when a hook is called outside a render.
- `use_ref` returns `reactpy.utils.Ref` with a single mutable `.current` attribute and a
  `set_current()` helper usable inside lambdas (`utils.py`, `Ref`). Not a DOM node handle.
- `create_context` returns a **function used as the provider**:

  ```python
  theme_context = create_context("light")
  ...
  return theme_context({"value": "dark"}, html.div(...))   # children, then value= keyword
  use_context(theme_context)
  ```
  Signature: `context(*children, value=default_value, key=None)` (`core/hooks.py`, `create_context`).
  Reading outside a provider returns the default value.

## 6. Context / connection

- `Connection` is a dataclass: `scope`, `location`, `carrier` (`types.py`).
- `Location` is a dataclass: `path`, `query_string` (`types.py`).
- `use_connection()` raises `RuntimeError: No backend established a connection.` when no
  backend set the context (`core/hooks.py`, `use_connection`).
- The backend establishes it; docs should not promise a specific `carrier` type.

## 7. Rendering / lifecycle

- `Layout(root_component)` is the core renderer: an async context manager with
  `await layout.render() -> LayoutUpdateMessage` and
  `await layout.deliver({"type": "layout-event", "target": ..., "data": [...]})`
  (`core/layout.py`, `Layout`). Not part of the `reactpy` top-level import.
- `render()` blocks until an update exists and returns `{"type": "layout-update",
  "path": <JSON pointer>, "model": ...}` — ReactPy **patches a subtree**, it does not resend
  the whole tree (`types.py: LayoutUpdateMessage`).
- `REACTPY_ASYNC_RENDERING` defaults to **True** (`config.py`); renders may be
  concurrent and stale renders for the same component are dropped.
- Event handlers run **sequentially per target** via a per-target queue
  (`layout.py: _process_event_queue`; `test_event_queue_sequential_processing`).
- Reconciliation matches children by key (missing keys fall back to the child's **index**),
  and a component is matched by its **function object identity**:
  `old_state.life_cycle_state.component.type != component.type` triggers
  `_unmount_model_states` + a fresh `_make_component_model_state`, destroying state
  (`core/layout.py`, `Layout._render_component`). Consequence worth teaching: a component
  **defined inside another component** gets a new function object on every parent render, so
  it remounts and loses all state each time — the ReactJS "never nest definitions" pitfall
  applies to ReactPy for exactly this reason.
- Duplicate keys are a hard error: `ValueError: Duplicate keys [...] at '<patch_path>'`
  (`core/layout.py`, `_render_model_children`).
- Unmount order is reversed (`layout.py: _unmount_model_states`), and each unmounting
  component stops its effect tasks and runs their cleanups.
- Non-str, non-dict, non-Component children are coerced with `f"{child}"`
  (`layout.py: _process_child_type_and_key`) — ints/floats render as text; so do `True`
  and `None`→skipped. `component_to_vdom` coerces a bare `str` return into
  `html.div(text)` (`utils.py: component_to_vdom`).
- **Booleans are NOT React-like.** Verified through `Layout.render()`: `False` renders as the
  literal text `"False"` and `True` as `"True"` (React renders both as nothing). Only `None`
  and an *empty list* are skipped. So the React idiom `{cond && <X/>}` becomes
  `*([] if not cond else [X])` — never `cond and X`. Likewise `count and html.p(...)`
  renders `"0"` when `count == 0`, reproducing the classic JS bug with no fix-up operator
  available. Do not port any `&&`-rendering example as if it worked.

## 8. Config

`reactpy.config.REACTPY_*` are `Option` objects; read/assign with `.current`
(e.g. `config.REACTPY_WEB_MODULES_DIR.current` in `tests/test_html.py`).

`REACTPY_DEBUG` (False, master switch), `REACTPY_CHECK_VDOM_SPEC`,
`REACTPY_CHECK_JSON_ATTRS` (both parented to DEBUG), `REACTPY_WEB_MODULES_DIR`,
`REACTPY_TESTS_DEFAULT_TIMEOUT` (15.0), `REACTPY_ASYNC_RENDERING` (True),
`REACTPY_RECONNECT_INTERVAL` (750), `REACTPY_RECONNECT_MAX_INTERVAL` (60000),
`REACTPY_RECONNECT_MAX_RETRIES` (150), `REACTPY_RECONNECT_BACKOFF_MULTIPLIER` (1.25),
`REACTPY_PATH_PREFIX` (`/reactpy/`), `REACTPY_MAX_QUEUE_SIZE` (1000).
All settable by env var (`reactpy/config.py`).

## 9. Executors / HTML conversion

- `from reactpy.executors.asgi import ReactPy` — SSR ASGI app;
  `ReactPy(hello_world)` (`docs/examples/creating_a_react_app/asgi_ssr.py`).
- `ReactPyCsr(Path(...) / "root.py", initial="Loading...")` — client-side rendering via
  PyScript; takes a **path to a module**, not a component
  (`docs/examples/creating_a_react_app/asgi_csr.py`).
- `ReactPyMiddleware` wraps an existing ASGI app; `path_prefix=...` sets the base path
  (`docs/src/learn/add-react-to-an-existing-project.md:17-21`).
- `reactpy_to_string(vdom_or_component) -> str` and
  `string_to_reactpy(html, *transforms, strict=True, intercept_links=True) -> VdomDict`
  replace the ReactJS-era `to_html_string` / `html_to_vdom` names (`utils.py`).
  `string_to_reactpy` raises `HTMLParseError` on malformed HTML unless `strict=False`, and
  `ValueError: Expected html string to contain HTML tags, but no tags were found.` on
  tag-less text.
- WSGI and SSG executors are **not shipped**; both are documented as "coming in a future
  version" with issue links (#1260, #1272).

## 10. Testing helpers (for examples we claim work)

`from reactpy.testing import DisplayFixture, poll, DEFAULT_TYPE_DELAY`.
`display.show(root_component)`, `display.page` is a Playwright page.
`reactjs` support and `tests/test_reactjs` exist for React-parity checks.

---

## 11. Docs house style (this repo, `new-docs` branch)

- Pages live in `docs/src/`; `docs/mkdocs.yml` `nav:` lists them. Add `🚧` to the nav
  entry of any page not yet migrated — and **remove `🚧` when you finish a page**.
- Prose is ReactJS-derived: **rewrite, do not rename**. Delete JSX-specific sections
  (no PSX/JSX in v2: `writing-markup-with-psx.md` and
  `python-in-psx-with-curly-braces.md` are `Planned / Undeveloped`).
- Structure per page: `## Overview`, then

  ```markdown
  <p class="intro" markdown>

  ...

  </p>

  !!! summary "You will learn"

      -   bullet
  ```
- Admonitions in use (Material + `assets/css/admonition.css`): `!!! summary "You will
  learn"`, `!!! abstract "Note"`, `!!! warning "Pitfall"`, `!!! info "Deep Dive"`,
  `!!! example "Terminal"`. ReactJS `<Pitfall>`/`<DeepDive>`/`<Recap>`/`<Challenges>`/
  `<Solution>`/`<Hint>` JSX tags have no MkDocs equivalent — convert to admonitions or
  plain headings, never copy them through.
- Links: relative `.md` paths (`../reference/use-state.md`), not `/learn/...`.
- Code fences: ` ```python linenums="0" ` for fragments; ` ```python ` (numbered) for the
  full-file tabs. `hl_lines="3-4 7"` marks highlighted lines.
- Runnable snippets are **extracted from real files** in `docs/examples/<page_slug>/`:

  ```markdown
  {% include "../../examples/quick_start/my_button.py" start="# start" %}
  ```
  `start="# start"` renders everything after that marker; `end="# end"` stops before its
  marker (see `examples/quick_start/updating_the_screen_use_state.py`). Full-file includes
  have no marker. Whole examples go in tabbed blocks:

  ```markdown
  === "app.py"

      ```python
      {% include "../../examples/<slug>/x.py" %}
      ```

  === ":material-play: Run"

      ```python
      # TODO
      ```
  ```
  The `:material-play: Run` tab is a standing placeholder — keep it.
- Example files are black-formatted, line length 88, imports at top, `# start` marker on
  its own line. `docs/**/*.py` ruff-ignores `E402`, `S102`, `T201` (`pyproject.toml:123`).
- Spellcheck plugin is disabled but `docs/src/dictionary.txt` exists; add new domain words
  there if you re-enable it.
- Changelog (`CHANGELOG.md`) gets an entry **only for user-facing changes**; docs work does
  not qualify unless shipped in a release.

## 12. Recurring migration traps

1. `className`, `onClick`, `key` stay **camelCase inside the attribute dict**. `class_name`
   is wrong. Only *Python identifiers we define* (functions, variables, components) are
   snake_case.
2. `set_state` **does** take an updater callable — do not claim otherwise. It runs
   **eagerly inside the setter** (`hooks.py`, `_CurrentState.dispatch` → `new(self.value)`),
   not during render, so its result is visible on the very next line.
3. `use_effect` + `async def` is a `TypeError`; async work needs `use_async_effect`.
4. `use_ref` gives `Ref.current`, never a DOM node.
5. No `useId`/`useTransition`/`useLayoutEffect`/etc. Do not port those pages as if real.
6. Component names are lowercase snake_case; there is no capital-letter rule.
7. Children never come from JSX nesting — they are positional args after the attr dict.
8. `event["target"]["checked"]` **works** — verified in a real browser (checkbox `onChange`
   yields `checked=True`). The stale "open bug / FIXME" claim in
   `docs/src/learn/thinking-in-react.md` is wrong; the client re-reads
   `value/checked/files/type/name` off the element with `in`, bypassing enumerability. See §4.
9. Generators as children skip key checking; use list comprehensions. Storing an
   **iterator in state is a severe bug**: `filter()`/`map()` return single-use iterators, so
   the first render shows the right items and every later render shows **nothing** (verified:
   state `["a","b","c"]` -> `filter(...)` rendered `a,c`, then an unrelated state change
   rendered `''`). Always wrap in `list(...)` or use a comprehension. React's docs cannot warn
   about this because JS `filter()` returns an array.
10. Never reference `reactpy.backend.*`, `use_id`, or 1.x-era `vdom()`/`Html()` APIs; they
    are not in v2.0.0b13's public surface.
11. Keep `@component` definitions at module level. A nested definition is a new function
    object per render, so ReactPy remounts that subtree and wipes its state (§7).
12. `class App()` / class-based components do not exist in v2 — components are functions.
13. **No `StrictMode`, and no double-invoke.** `StrictMode` is absent from the package and the
    layout never calls a component twice, so React's "impure components render #2/#4/#6"
    symptom cannot be reproduced. Port StrictMode sections as a warning that ReactPy will not
    catch impurity for you, and suggest a render-twice test instead.
14. **No component-level `memo`.** `reactpy.memo` does not exist (only `use_memo` for values),
    so a child re-runs whenever its parent renders — verified by counting calls across a
    `use_state` update. Do not claim React's "skip rendering unchanged inputs" optimization.
    `reactpy_to_string` (in `reactpy.utils`) does exist and is the server-render story, but it
    leaks module-level state across calls, which is a purity argument, not a feature.
15. **`set_state` replaces; it never merges.** `dispatch` does `self.value = next_value`
    (`hooks.py`, `_CurrentState.dispatch`) with no dict merge — verified: setting
    `{"a": 9}` over `{"a": 1, "b": 2}` yields `{'a': 9}`, so `b` is gone. Same as React's
    `useState` (unlike class `setState`), so ReactJS prose saying "React merges the object
    into your current state" is wrong for ReactPy and must not be ported. Partial updates
    require `set_x({**x, "k": v})`.
16. **Mutating in place then setting the same object is silently dropped.** Identity
    comparison in `dispatch` means `x.append(i); set_x(x)` schedules **no render** at all —
    verified. No error, no console output, no warning; the handler runs and the UI never
    changes. Also covers mutating without calling the setter.
17. **`use_state` facts to state plainly.** The setter is a stable object (verified: 4
    renders, 1 distinct setter) so it is safe in dependency arrays and as a prop. `State` is
    a `NamedTuple` `(value, set_value)`, so unpacking works. The initial value may be a
    zero-arg callable and runs **once** (verified: 1 call across 4 renders) — but that means a
    *function you want to store* is treated as an initializer: `use_state(lambda x: x * 2)`
    raises rather than storing the lambda. Store functions in `use_ref` instead.
18. **A conditional/reordered hook is silent corruption, not an error.** Adding an extra hook
    on some renders produces `IndexError: list index out of range` captured into the model's
    `error` field (verified); ReactPy has no "Rendered fewer hooks than expected" guard, so
    never port React's hook-order warnings as if the check exists.
19. **Resetting state via `key` works and is the documented idiom.** Verified in a real
    browser: a child rendered with `key="a"` bumped to `a:2` then re-rendered with
    `key="b"` came back at `b:0`, while the same child rendered *without* a key kept its
    count (`b:2`).
20. **Handlers receive exactly one positional argument.** The event is `data[0]` unpacked
    onto the signature; a handler declaring two required parameters raises
    `TypeError: ... missing 1 required positional argument: 'event'` — verified. There is
    no `e.target.name`: the client does not send DOM attributes, so extra context must be
    bound in Python (usually a `lambda`). Pointer events DO carry `clientX`/`clientY`
    (browser-verified), so drag/pointer demos are portable.
21. **Batching is sync-only.** A plain `def` handler making several setter calls produces
    **one** render; an `async def` handler that `await`s between them produces **one render
    per flush** (measured in Chrome: `0→3` vs `0→1→2→3`), because `dispatch` assigns state
    immediately and only flags a re-render. React 18+ batches both. Never claim React-style
    batching across `await`.
22. **A raising updater is swallowed.** If an updater raises, state is left unassigned, no
    render is scheduled, and `Layout._process_event_queue` logs `Failed to execute event
    handler` server-side while the browser stays silent. Check the server log when a control
    "stops working" with no client error.
23. **Equal state does not re-render.** `dispatch` compares with `strictly_equal` (identity,
    except int/float/complex/str/bytes/bytearray/memoryview by value) and skips
    `schedule_render()` when equal — verified. But this is *not* component memoization: see
    item 14.
24. **Effects infer their dependencies by default — this is NOT React.** With no
    `dependencies` argument, `use_effect` calls `_try_to_infer_closure_values`, so deps come
    from the closure's *free variables* (`core/hooks.py`). Verified: a closure referencing no
    local variables runs **once**; one referencing `n` re-runs when `n` changes; one
    referencing only the stable setter runs once. `dependencies=[]` runs once,
    `dependencies=[n]` re-runs on change, `dependencies=...` means "infer". Never port React's
    "omit the array to run after every render" — it is wrong here.
25. **`use_async_effect` takes a ZERO-argument coroutine.** It does `create_task(func())`
    (`core/hooks.py`), so the 1.x `async def effect(stop)` shape is *silently* broken: the
    `TypeError` is logged as `Error in effect` while the component still renders. Long-running
    work is `while True:` + `except asyncio.CancelledError`, never a `stop` event.
    `shield=True` lets an in-flight effect finish after unmount; the default `shield=False`
    cancels it — both verified.
26. **Effect ordering: children before parent, siblings in REVERSE order.** Verified output
    `['child effect b', 'child effect a', 'parent effect']`. Two effects in one component run
    in declaration order. Do not promise React's parent-first or source-order semantics.
27. **`use_effect` rejects `async def` loudly** — the `TypeError: use_effect does not support
    async functions. Use use_async_effect instead.` lands in the model's `error` field. An
    effect body that raises at runtime is logged server-side only, with nothing in the model.
28. **Dependency comparison is *not* identity-based** — `reactpy.core.hooks.strictly_equal`
    backs every dependency array (`use_effect`, `use_memo`, `use_callback`). It is *not* the
    `id()` comparison the docstrings claim. For two callables whose `__qualname__` contains
    `<lambda>` or `<locals>`, it compares all `co_*` code attributes (ignoring line/column
    metadata), so a structurally identical nested function or lambda is treated as **unchanged**
    across renders. For everything else it tries `==` first and only falls back to `is` when
    `__eq__` is missing or raises. Consequences, all measured: a dependency that is a fresh
    `list`/`dict` with equal contents does **not** re-trigger the effect; a fresh object of a
    plain class (default identity `__eq__`) **does**; a structurally identical local `def`
    handler does **not** — so an effect listing it as a dependency keeps the closure it first
    captured and reads stale state. Do not teach React's identity semantics here.
29. **There is no render bailout at all.** A child component's body re-runs whenever its parent
    re-renders, even with unchanged props, and even when the element is cached in `use_memo`
    (`use_memo(lambda: child(x), dependencies=[x])` still re-executes `child`). ReactPy's layout
    has no `should_render`/bailout path, and there is no `memo`. Docs must not promise that
    `use_memo`/`use_callback` "prevent the child from re-rendering"; they only avoid *recomputing*
    a value or *re-registering* an effect.
30. **`use_ref` is server-side only — there is no DOM ref.** `reactpy.utils.Ref` is a one-field
    mutable box (`current`, plus `set_current()` which returns the old value, handy in a
    `lambda`). It survives renders as the *same object*. There is no `ref_current`, no
    `ref_current_callback`, and no attribute that hands a browser DOM node to Python: neither the
    package nor `static/index*.js` references them, and a rendered `{"ref_current": ...}` is an
    inert unknown attribute (verified in Chrome — the element is not found by that id). Never
    port React's `useRef` DOM examples (focus, scroll-into-view, video play/pause); port
    `use_ref` as a value box, and say so.
31. **`use_memo`/`use_callback` infer dependencies like `use_effect`** — all three default to
    `dependencies=...` and call `_try_to_infer_closure_values`. With inference active, a compute
    function that reads only `a` is not recomputed when unrelated state changes; `dependencies=[]`
    pins the value forever (and pins a callback's identity forever, so a callback closed over
    state goes stale); `dependencies=None` recomputes every render.
32. **Mutate-then-set-the-same-object also defeats `use_memo`.** `rows.append(x)` followed by
    `set_rows(rows)` changes nothing observable: no re-render *and* no `use_memo` recompute,
    because the dependency compares equal to itself. Same root cause as the `use_state`
    drop-the-update rule; state must be replaced with a new object.
33. **Probing hook behaviour needs an event-loop yield.** Effects run in their own task, so a
    `Layout` probe that reads a log right after `await layout.render()` sees nothing. Insert
    several `await asyncio.sleep(0)` calls after each render before asserting. Also note a second
    `await layout.render()` with nothing pending blocks until timeout — wrap it in
    `asyncio.wait_for`.
