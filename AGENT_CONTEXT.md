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
- `key` goes in the attribute dict for elements: `html.li({"key": product["id"]}, ...)`
  (`docs/examples/quick_start/rendering_lists_list_items.py:6`).
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
- Supported payload reads proven by tests: `event.target.value`
  (`test_events.py: test_controlled_input_rapid_typing`,
  `test_controlled_input_respects_custom_debounce`).
  `event["target"]["checked"]` is **not** proven by any test — `thinking-in-react.md:223`
  carries `FIXME: Click event on the checkbox is broken. event["target"]["checked"] doesn't
  exist`. Do not document `checked` as working.
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
2. `set_state` **does** take an updater callable — do not claim otherwise.
3. `use_effect` + `async def` is a `TypeError`; async work needs `use_async_effect`.
4. `use_ref` gives `Ref.current`, never a DOM node.
5. No `useId`/`useTransition`/`useLayoutEffect`/etc. Do not port those pages as if real.
6. Component names are lowercase snake_case; there is no capital-letter rule.
7. Children never come from JSX nesting — they are positional args after the attr dict.
8. Do not present `checked` on checkbox events as working (open bug, see §4).
9. Generators as children skip key checking; use list comprehensions.
10. Never reference `reactpy.backend.*`, `use_id`, or 1.x-era `vdom()`/`Html()` APIs; they
    are not in v2.0.0b13's public surface.
11. Keep `@component` definitions at module level. A nested definition is a new function
    object per render, so ReactPy remounts that subtree and wipes its state (§7).
12. `class App()` / class-based components do not exist in v2 — components are functions.
