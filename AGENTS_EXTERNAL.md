# ReactPy v2.0.0 — Agent Context (external projects)

Compact reference for an agent **writing or reviewing a ReactPy app that depends on the
`reactpy` package**. Every claim is checked against `src/reactpy/` and `docs/src/` at
`reactive-python/reactpy@main` (package version `2.0.0b13`; the published wheel may lag —
verify against your installed version before relying on a detail).

Out of scope on purpose: developing ReactPy itself (its tests, packaging, and docs sources), and
anything about porting React documentation. If you are working *inside* the ReactPy repository,
this file is the wrong reference.

**Rules for code you emit:** `snake_case` for everything you name, never invent an API,
keep snippets runnable, and never port a React idiom without checking the "differs from
React" notes here.

---

## 0. Read this first — where React's instincts are wrong here

1. **Event handlers must be `async def`.** A plain `def` raises `TypeError` at tag-construction time.
2. **There is no `&&` rendering.** `True`/`False` render as the text `"True"`/`"False"`; only `None` renders nothing.
3. **A component returns exactly one thing** — an element, a component instance, a `str`, or `None`. Returning a list or tuple renders its Python `repr`.
4. **State is replaced, never merged**, and an in-place mutation is dropped *silently* — no error, no warning.
5. **Effects can infer their dependencies.** `dependencies` has four meanings: omitted (infer from the closure's free variables), `[]` (never again), `[a, b]` (on change), `None` (every render) — and a bare `@use_effect` decorator silently means the last one.
6. **Hook state is positional.** Changing *which* hooks run usually does not raise — a component quietly reads its neighbour's value.
7. **There is no memoization bailout.** A child re-renders whenever its parent does; `use_callback`/`use_memo` cannot stop that.
8. **There is no `StrictMode` and no double-render**, and module scope is **shared by every visitor in the process** — a module-level `dict`, list, element, or `my_component.started` flag leaks between users. Purity is not style advice.
9. **There is no DOM access.** No refs to nodes, no `document`, no `window`; `{"ref": ...}` does nothing useful (a `dict` is ignored, a `str` throws in the browser).
10. **Errors are server-side.** A handler or effect that raises leaves a dead button with nothing in the browser console. Run with `REACTPY_DEBUG=1` and read the server log.

---

## 1. Install, package, run

- Python **>= 3.11**. Package is `reactpy`. Core deps: `fastjsonschema`, `requests`, `lxml`, `anyio`.
- Extras: `asgi` (`asgiref`, `asgi-tools`, `servestatic`, `orjson`) · `jinja` (`jinja2-simple-tags`, `jinja2>=3`) · `testing` (`playwright`, `uvicorn[standard]`) · `all` = the three.
- `pip install "reactpy[asgi]" "uvicorn[standard]"`. Without the extra, importing an executor raises
  `ModuleNotFoundError: ASGI executors require the 'reactpy[asgi]' extra to be installed.`
- There is **no CLI workflow and no build step**. You write the ASGI app yourself and hand it to any ASGI server:

  ```python
  # main.py
  from reactpy import component, html
  from reactpy.executors.asgi import ReactPy

  @component
  def hello_world():
      return html.div("Hello World")

  my_app = ReactPy(hello_world)   # module-level variable: uvicorn refers to it by name
  ```

  ```bash
  uvicorn main:my_app
  ```
- ReactPy **serves components, not files on your disk**. A `styles.css` next to `main.py` is not served; read it and inject it: `ReactPy(app, html_head=html.head(html.style(Path("styles.css").read_text())))`, or point a `<link>` at your own static route.
- Not shipped: WSGI, SSG, native apps (issues #1260, #1272, #570). Django goes through the separate **`reactpy-django`** package, not `reactpy.executors.asgi`.
- Shipped console script: `reactpy rewrite-props PATHS...` (rewrites snake_case prop keys to camelCase across `*.py`). Needs `click`, which is not a core dependency.

---

## 2. Public surface

`reactpy/__init__.py` — all importable as `from reactpy import X`:

```python
from reactpy import (
    component, create_context, event, h, html, hooks, use_async_effect,
    use_callback, use_connection, use_context, use_debug_value, use_effect,
    use_location, use_memo, use_reducer, use_ref, use_scope, use_state,
    widgets, types, config, logging, reactjs, web,
    Ref, Vdom, reactpy_to_string, string_to_reactpy, pyscript_component,
)
```

Prefer `from reactpy import component, html` — the shape every documented example uses.
`reactpy.hooks` and `reactpy.utils` are reachable as **attributes** (`reactpy.hooks.use_state`,
`reactpy.utils.Ref`) but `reactpy.hooks` is an alias, not a module: `import reactpy.hooks` and
`from reactpy.hooks import use_state` raise `ModuleNotFoundError`. Use `reactpy.core.hooks` in
an import statement. `h is html` is `True` — pick one per file.

Other import paths you will actually need:

| Name | Import from |
| --- | --- |
| `ReactPy`, `ReactPyCsr`, `ReactPyMiddleware` | `reactpy.executors.asgi` |
| `server_side_component_html` | `reactpy.executors.utils` |
| `ReactPyJinja` | `reactpy.templatetags` |
| `component_from_npm` / `_url` / `_file` / `_string`, `import_reactjs` | `reactpy.reactjs` |
| `Layout` | `reactpy.core.layout` |
| `EventHandler` | `reactpy.core.events` |
| `VdomDict`, `VdomAttributes`, `Context`, `Connection`, `Location`, `EventHandlerDict` | `reactpy.types` |
| `Ref` (low-level box) | `reactpy.utils` |
| `ConnectionContext` (test injection) | `reactpy.core.hooks` |
| `DisplayFixture`, `poll` | `reactpy.testing` (`reactpy[testing]`) |

**Hooks that exist (13):** `use_state`, `use_effect`, `use_async_effect`, `use_reducer`,
`use_context`, `use_ref`, `use_memo`, `use_callback`, `use_debug_value`, `use_connection`,
`use_scope`, `use_location`, plus `create_context`.

**Hooks and APIs that DO NOT exist — never emit them:**
`useTransition`/`use_transition`, `useDeferredValue`, `useId`, `useLayoutEffect`,
`useImperativeHandle`, `useInsertionEffect`, `useSyncExternalStore`, `useOptimistic`,
`useActionState`, `useEffectEvent`, `useEvent`, `forwardRef`, `flushSync`, `memo`,
`createPortal`, `StrictMode`, `defaultProps`.
There is also no PSX/JSX (#918), no React Developer Tools equivalent (#1072), and no Immer
equivalent. A function whose name starts with `use` but which you did not get from this list
is a hallucination.

---

## 3. Components

```python
@component
def my_button():
    return html.button("I'm a button!")
```

- `component(function)` is a plain decorator, no options (`core/component.py`).
- **Names are `snake_case`.** React's "must start with a capital letter" rule does not apply:
  ReactPy distinguishes components from tags by *call*, not by case.
- `@component` makes a **constructor**. `type(my_button())` is `reactpy.types.Component`;
  the function body runs later, when the layout renders it.
- **Pass the function, never call it as a child.** `html.div(my_button)` renders
  `<function my_button at 0x...>` as page text — a hex address on the page means a missing call.
- **Return exactly one value**: a VDOM dict, another component instance, a `str`, or `None`
  (`utils.py: component_to_vdom`). `return a, b` or `return [a, b]` renders the tuple/list
  **repr** as text. For several top-level children use `html.fragment(...)` or a real element.
- `key` is a **reserved parameter**: declaring one raises at *decorate* time —
  `TypeError: Component render function <...> uses reserved parameter 'key'`.
  `*args`/`**kwargs` are allowed, and you cannot smuggle `key` in through `**props` (the
  constructor swallows it).
- **Define components at module level.** A component defined inside a function is a new
  function object each render, so `old.type is not new.type` and ReactPy unmounts and rebuilds
  its subtree every render (`core/layout.py`). State is lost. The `reactpy-flake8` code for
  this is `REACTPY100`.
- Calling `my_component().render()` outside a layout raises
  `RuntimeError: No life cycle hook is active. Are you rendering in a layout?`
  To inspect output, render inside a `Layout` (see §25).
- Components are values: build them in a loop, pass them as props, put them in a list.
  `one = my_button(); html.div(one, one)` is *not* one shared component — it is two positions,
  therefore two independent states.
- Props are read-only in effect: assigning to a parameter rebinds your local name only.
- ReactPy does not care which module defines a component and has no default/named export
  distinction; there is no global component registry, so a component used by two modules must
  be imported in both.
- Wrap multi-line elements in parentheses; never use a backslash continuation.

## 4. Props and children

- Props are ordinary Python parameters; every declared parameter is a prop a caller can pass
  by name. There is no props object and no `children` prop — **positional args are children**:

  ```python
  @component
  def card(*children):
      return html.div({"className": "card"}, *children)

  @component
  def card(*children, title=None):          # props keyword-only: can't be mistaken for a child
      return html.div({"className": "card"}, title, *children)
  ```
- Prop defaults are plain Python defaults: they apply only when the caller **omits** the
  argument. `size=None` or `size=0` does not fall back to the default. No `defaultProps`.
- Forwarding: `@component def profile(**props): ... avatar(**props)`. `props` is an ordinary
  dict you can filter or merge — use sparingly, it hides the interface.
- Props may be any Python value (dicts, lists, functions). Passing a setter or `dispatch` down
  as a prop is the documented way for a child to update the parent.
- Lift state to the lowest component that needs all of it; when two components need the same
  value, lift to their nearest common ancestor. "Controlled" = driven by props,
  "uncontrolled" = driven by its own `use_state`.

## 5. HTML and VDOM

`html` resolves any attribute through `__getattr__` (`_html.py`). The tag name is
`value.rstrip("_").replace("_", "-")` applied blindly: trailing `_` stripped, **every** `_`
becomes `-`, leading `_` is not special (`html._x` → `-x`), doubles are not collapsed
(`html.a__b` → `a--b`), and case is preserved. Constructors are cached, so `html.div is html.div`.

```python
html.div("Click me")                                 # children only
html.div({"class": "x"}, "Click me")                 # attributes dict first
html.div(None, child_a, child_b)                     # explicit "no attributes"
```

- Attributes are taken **only** when the first argument is an exact plain `dict`. A
  `VdomDict` — or any other `dict` **subclass** — in that position is a *child*; a dict in any
  later position is always a child. `html.div({"children": ["x"]})` sets an attribute literally
  named `children`.
- Element children flatten **recursively** (`vdom.py: _flatten_children`): `html.div([[["a"], "b"]])`
  yields `children == ["a", "b"]`. (This is *element children* — a component's *return value*
  does not flatten; see §3.)
- Children may be strings, numbers, `None`, lists/tuples, dicts, component instances.
  `int`/`float` render as text; `True`/`False` render as `"True"`/`"False"`; only `None` and an
  empty list contribute nothing.
- Conditional child — **never** `cond and X` (a falsy `0`/`""` renders, a `False` renders as
  text). Use one of:
  ```python
  html.li(name, *(["✔"] if is_packed else []))
  html.li(name, html.del_(f"{name} ✔") if is_packed else name)
  content = [name]
  if is_packed:
      content.append("✔")
  return html.li(*content)
  ```
  For a **state-reset placeholder** an empty expansion is wrong: `*([] if not cond else [X])`
  contributes *zero* children, so both branches land at index 0 and no reset happens. Use a
  real container that is always present: `html.div(counter("Taylor") if is_player_a else None)`.
- Unpacking traps: `html.div(*some_vdom_dict)` prints the dict's **keys** as text (when
  `some_vdom_dict` came from an undecorated function), and `*my_component()` raises
  `TypeError: ... argument after * must be an iterable, not Component`. If the page shows a
  Python repr, suspect a missing call, a stray comma, or a stray `*`.
- **Void HTML tags reject children** (`area base br col command embed hr img input iframe
  keygen link meta param portal source track wbr`) → `TypeError: 'br' nodes cannot have children.`
- **Void SVG is much larger than you expect** (56 names in `NO_CHILDREN_ALLOWED_SVG`) and
  includes `text`, `tspan`, `textPath`, `title`, `desc`, `path`, `use`, `rect`, `circle`,
  `line`, `image`, `style`, `filter`, `foreignObject`, `script`, all `animate*`/`fe*`. So
  `html.svg.text("hi")` raises. Build those with `Vdom("text")("hi")`.
- `html.svg.script(...)` also raises — the SVG namespace has no `script` special case.
- Any name is a valid tag; nothing is validated, so `html.hdeader("x")` renders an unknown
  element in silence. For names that can't be attributes, use
  `Vdom("2fa-code")("123456")` — same class every `html.*` name is built from
  (`Vdom(tag_name, /, allow_children=True, custom_constructor=None, import_source=None)`).
- `html(...)` / `html.fragment(...)` is the fragment: `tagName == ""`, and it rejects anything
  but `key` — including handlers: `TypeError: Fragments cannot have attributes besides 'key'`.
- `html.script` special cases: at most one child, must be a `str`, no event handlers
  (`ValueError: 'script' nodes may have, at most, one child.` / `... must be a string.` /
  `'script' elements do not support event handlers`). With no `key`, one is inferred from the
  script text, else from `src` — pass your own `key` to control re-execution. Nothing is
  escaped; never interpolate untrusted text.
- **A built element has no `attributes` key when there are none** (`html.div("x")["attributes"]`
  → `KeyError: 'attributes'`; same for `children`, `eventHandlers`, `inlineJavaScript`,
  `importSource`). Mutating by hand goes through `element.setdefault("attributes", {})["id"] = "a"`.
  Constructors copy the **top level only**: `element["attributes"] is not your_dict`, but nested
  values and child elements you built earlier are stored **by reference**.
- Mutating an element inside an event handler is invisible until something else renders — the
  change appears on the next unrelated click. That is not a timing bug: nothing re-rendered.
- A **module-level element is one dict shared by every connection in the process** (unlike React's
  per-tab module scope): one visitor's handler mutates everyone's page. Build elements inside the
  component (a `def status_banner(text, tone): return html.p(...)` helper); module constants are
  fine only if nothing ever writes to them. `copy.deepcopy` is the right tool for forking a parsed
  template — it preserves the `VdomDict` guard, but builds a *new* `EventHandler` sharing the same
  function, so it is not a way to give two elements independent handlers.
- The client builds elements with `createElementNS`, so SVG attribute names are forwarded
  verbatim — write `viewBox`, not `viewbox`.
- Tag calls never validate attribute names: `html.img({"scr": ...})` is a silent no-op. Only
  `class`/`className` and `for`/`htmlFor` have aliases.

## 6. What goes in the attributes dict

Only `tagName` is required on the resulting `VdomDict`. Keys: `children`, `attributes`,
`eventHandlers`, `inlineJavaScript`, `key`, `importSource`, `error` — and nothing else is read
(`core/vdom.py` does not reject unknown keys; only debug-mode schema checks do).

- **Attribute names are not validated and nothing is rewritten** (no `tabindex`→`tabIndex`, no
  `class`→`className`). If the browser understands it, ReactPy delivers it: `data-*`, `aria-*`,
  everything else. `class` and `className` both produce `class=`; `for` and `htmlFor` both
  produce `for=`. Prefer one and stay consistent.
- **Values must be JSON-serializable.** Nothing filters them first, so an unserializable value
  fails where you will not expect it: `TypeError: Type is not JSON serializable: coroutine` from
  the frame encoder (orjson) deep in the connection, with the element unnamed. Under
  `REACTPY_CHECK_JSON_ATTRS` (which follows `REACTPY_DEBUG`) it fails at the tag call instead,
  where the element is visible.
- **Attribute values are not validated at all.** The v2 schema (`core/vdom.py:
  VDOM_JSON_SCHEMA`) requires only `tagName` and shapes `eventHandlers` (`target` required;
  `preventDefault`/`stopPropagation`/`stopImmediatePropagation` booleans; **`debounce`/`throttle`
  integers ≥ 0**) and `importSource` (`source` required, `sourceType` ∈ `URL|NAME`) — and even
  that runs only under `REACTPY_CHECK_VDOM_SPEC`. So `None`, `False`, `0`, and a misspelled key
  all pass through and are handed to the DOM library to interpret. **Build the dict conditionally
  rather than setting a key to `None`/`False` to mean "absent"**, and read the rendered HTML when a
  flag "does nothing".
- **Booleans and numbers** follow the browser, not React: a non-empty string and `True` add the
  attribute (presence-only), `False` and `""` drop it, `0` adds `"0"`. A *required* control
  renders with `disabled`/`readonly` ignored. Read the rendered HTML when a flag "does nothing".
- **`style`** takes a `dict` with camelCase or kebab-case keys. **Always include the unit in the
  string**: `{"font-size": "30px"}` works everywhere; `{"fontSize": 30}` works under
  `ReactPy`/`ReactPyMiddleware` but renders nothing under `ReactPyCsr`; `{"fontSize": "30"}`
  renders nothing anywhere. (`zIndex`/`lineHeight`/`opacity`/`flex`/`order`/`zoom` are unitless.)
  ReactPy does not normalize a `style` *string* — pass a dict.
- **`dangerouslySetInnerHTML: {"__html": "..."}`** replaces children (children are discarded).
  Pass raw markup only; `{"__html": None}` and `{"__html": {"untrusted": snippet}}` are wrong —
  the second prints the dict's repr. ReactPy performs no sanitizing.
- **`key`** may live in the attributes dict (or be passed as `key=` at a component call). It is
  removed before reaching the DOM. An element with no key falls back to its **index** among
  siblings.
- Fragments are erased on the client, so a keyed fragment's children become plain siblings.

## 7. Keys

- Keys identify **position**, not value. Same component + same position → state preserved, even
  when props change; anything else at that position → state destroyed.
- Keys must be unique **among siblings** only. Reusing a value under a different parent is fine.
- Duplicate keys are a hard error in ReactPy (React only warns):
  `ValueError: Duplicate keys [1] at '/children/0'` — the whole component fails to render.
  An explicit **int key can collide with an unkeyed sibling** (unkeyed children take their
  index as key): `chat(to, key=0)` next to an unkeyed sibling at index 0 raises. Prefix keys
  (`key=f"chat-{to['id']}"`) or key every sibling.
- Never generate keys during render (`uuid.uuid4()`, `id(x)`, `next(count())`): keys never
  match, so every node and every piece of user input in the list is recreated each render.
  Keys come from the data. Index-as-key is acceptable only if items are never inserted,
  removed, or reordered.
- Components never receive `key`. Pass an ID alongside: `profile(id=id, key=id)`.
- Several nodes per list item → a keyed fragment: `html({"key": person["id"]}, html.h1(...), html.p(...))`.
- Keys do **not** resurrect state. An unmounted component's state is gone; to keep drafts,
  render everything and hide with CSS, or lift the state to a common ancestor, or store it
  outside ReactPy.
- Missing-key warnings only appear under `REACTPY_DEBUG`:
  `Key not specified for child in list row(7f2c11ac75e0, person={...})` (elements show
  `children: ...` to cut spam). A list can ship without keys and misbehave later.
- Pass a **list**, not a generator: `html.ul([html.li(p) for p in people])`. A generator has no
  length, so key integrity cannot be checked (debug mode warns) and it is consumed once.
- A list helper that forgets `return` renders nothing at all — `None` children are skipped,
  with no error and no log. Annotate helpers `-> VdomDict` so a type checker catches it.

## 8. Event handlers

A handler is an `async def name(event)` whose body runs **on the server**. Three buckets, by
**value kind, not key name** (`core/vdom.py: separate_attributes_handlers_and_inline_javascript`):

| Value | Lands in |
| --- | --- |
| anything `callable` | `eventHandlers` — **under any key name**; a non-coroutine raises |
| a `BaseEventHandler` | `eventHandlers`, stored as-is |
| a `str` under a key matching `^on[A-Z]\w+` | `inlineJavaScript` (eval'd in the page) |
| a `reactpy.types.InlineJavaScript` string | `inlineJavaScript`, under any key |
| everything else | `attributes`, verbatim |

- Naming: a handler is `handle_<event>` (`handle_key_down`). Your **own** components' callback
  props are ordinary snake_case parameters (`on_click=`, `on_play_movie=`) — only the built-in tag
  key is camelCase (`{"onClick": on_smash}`). A `lambda` is never a handler; bind extra context
  with a **handler factory** (`def handle_toggle(id): async def inner(event): ...; return inner`)
  or a named handler over a closure. Reading `await event.target.name` instead costs a round trip
  per click and only works if the element actually has a `name`.
- Python scoping bites where JS would not: mutating a plain variable from a nested
  `async def handle_...(event)` raises `UnboundLocalError` unless you declare `nonlocal`. Do not
  "fix" it that way — that is what `use_state` is for.
- **A plain `def` is rejected at the tag call**, and it is the *only* thing ReactPy checks about a
  handler: `<name> cannot be used as an event handler because it is not a coroutine. Event
  handlers must be declared with 'async def': …` (passing a state setter adds
  `A state setter is not an event handler - call it from one instead`). A `lambda` fails the same
  check because no lambda is a coroutine.
- **Nothing checks arity or the return value.** A handler taking zero parameters (or two required
  ones) constructs fine and blows up at dispatch — `Failed to execute event handler ...` in the
  server log with a dead button in the page. A handler that returns something is silently ignored
  (raise to signal failure). `@component`, `@hook`, and `@functools.wraps` preserve signatures and
  are safe.
- `{"onClick": True}` is **not** a handler (bools aren't callable) — no listener, no error.
  `{"onClick": handle_click()}` passes a coroutine *object*: it falls through to attributes and
  surfaces as `TypeError: Type is not JSON serializable: coroutine` plus
  `RuntimeWarning: coroutine ... was never awaited`. Pass the function, never call it.
- Handler names are irrelevant; only `on*` is documentation. What reaches the DOM is the
  `{key_path}:{event}` target suffix — `{"onclick": f}` listens for an event named `onclick`,
  never `click`. Unknown event names are registered silently and never fire.
- `@use_effect` / `@use_memo` / `@use_callback` used as decorators are traps:
  `use_effect(f)` returns `None` (the name stops being callable), `@use_memo(deps=...)` makes the
  name *the value* (`TypeError: 'int' object is not callable`), while
  `@use_callback(dependencies=[x])` correctly returns a function.
- **There is no tuple option form.** The ReactJS-era `{"onClick": (h, "target", True, ...)}` and
  `{"onClick": {"function": h, "preventDefault": True}}` are not callables, so they land in
  `attributes` and fail at serialization. Options come from `@event(...)` or `EventHandler(...)`
  only. `@event` (`core/events.py`, exported from `reactpy`) is **keyword-only**:
  `@event(stop_propagation=False, stop_immediate_propagation=False, prevent_default=False,
  debounce=None, throttle=None)`. It returns an `EventHandler` *value*, not a function.
  `EventHandler(function, stop_propagation=..., prevent_default=..., target=None, debounce=...,
  throttle=..., stop_immediate_propagation=...)` is the same with one extra knob, `target`.
- **Never pass `target=`.** ReactPy derives it per element (`f"{key_path}:{event}"`), which is
  exactly what lets one shared handler serve two buttons. A forced shared target makes the two
  elements overwrite each other, and unmount deletes the key twice → `KeyError` from
  `Layout._unmount_model_states`, leaving stale handlers. `@event` does not accept `target` at
  all. `merge_event_handlers` (unused inside the package) requires *every* option to match:
  `ValueError: Cannot merge handlers - 'stop_propagation', 'prevent_default', 'debounce',
  'throttle', 'target', or 'stop_immediate_propagation' mismatch.`
- **ReactPy reads your handler's bytecode** (`core/_event_inspect.py`) and turns what it finds
  into options, so writing the call is usually enough: `event.preventDefault()` →
  `prevent_default`, `event.stopPropagation()` → `stop_propagation`,
  `event.stopImmediatePropagation()` → both, `event.debounce = 250` → `debounce`. Detection is
  static (pattern matching on instructions, never executed) and **breaks silently** — the form
  still submits, the event still propagates — when: the event is not the *first* positional
  parameter; the handler takes no parameter; you rebind (`e = event; e.stopPropagation()`); you
  delegate (`await helper(event)`); the handler is `functools.partial`-bound over the event
  argument; or it is a bound method. Escape hatch: declare it, `@event(prevent_default=True)`.
  A handler factory (`def handle_toggle(i): async def inner(event) ...; return inner`) is safe —
  `inner` still leads with the event.
- **`debounce` and `throttle` both rate-limit the client→server send** (the `types.py` /
  `core/events.py` docstrings calling them server→client are stale — the shipped client
  contradicts them). Values are **milliseconds**; `throttle` is leading-edge and works on every
  element; `debounce` is strictly trailing-edge and is applied **only** to
  `input`/`select`/`textarea` — on a button or a `div` it does nothing, silently. There is no
  default for either. A value the client cannot validate (`isValidDebounce`) leaves the handler
  un-wrapped with no error.
- **Detection of `event.debounce = <value>` resolves only** an int literal, a compile-time-folded
  expression (`100 * 5`), a numeric parameter *default*, or a numeric closure cell. A module-level
  global, a plain parameter, or an arbitrary expression taints the whole detection to `None`.
  `throttle` is never detected — pass it explicitly.
- **Inline JavaScript**: a string under `onXxx` is `eval`'d with `event`, `element`, and
  `ReactPy` in scope; its return value is the payload. Always `return;` unless you want the
  return sent to the server as `data[0]`. Call `event.preventDefault()` *in the JS string* —
  the Python call only mutates a server-side copy. Never interpolate user input into the string.
  A lowercase `{"onclick": "..."}` is a plain attribute that never fires. This is the sanctioned
  escape hatch for focus/scroll: give the element an `id` and use
  `{"onClick": "document.getElementById('my-input').focus(); return;"}`.

## 9. The event object

`Event` is an `EventProxy` (`_event_proxy.py`), **not a dict**:

- `event["target"]["value"]` raises `TypeError: 'Event' object is not subscriptable` — the
  client no longer serializes the event. `await event.target.value` is the only way.
- **No `__getitem__`, `__len__`, `__iter__`, `__contains__`.** `if not event:` is always `False`;
  `"target" in event` raises `TypeError: argument of type 'Event' is not iterable`.
- Every read is an `await` and costs a round trip; attributes are `EventProxy` objects, values
  arrive only on `await`. Reads are cached per `event_id`+path (re-read is free, but the value
  is a snapshot). Batch with `await event.read("type", "target.value", "target.checked")` or
  `asyncio.gather(event.target.value, event.target.checked)` — one message.
- `await event` → whole native object; `await event.path` → frozen path tuple;
  `await event.composedPath()` → list; `event.preventDefault()` / `stopPropagation()` /
  `stopImmediatePropagation()` are **sync** and mutate a local copy of the flags;
  `event.defaultPrevented` / `event.propagationStopped` resolve local ∪ client state.
  Anything else is a read of the native `Event`, including `await event.target.name`.
- **Do not hold an `Event` past the handler** — across `asyncio.gather`, in a `use_ref`, or in
  module state. Each handler gets its own handle, pruned on a client-side LRU.
- Methods are references: `await event.target.foo` is an `EventProxyMethod`; call it as
  `await event.target.foo(a, b)`. Accessing a method you then only `await` (never call) returns a
  reference.
- `await event.target` on `<input type="file">` gives **metadata only** (name, size, type,
  lastModified) — never bytes, because `File.text()` is a method. On `<form onsubmit>` it gives
  the form; iterating it (or `await event.target.elements`) yields one plain dict per control,
  so `c["name"]`/`c["value"]` work.
- **Never duck-type the proxy.** `__getattr__` hands back a truthy `EventProxy` for *any* name
  (only `_reactpy*` and dunders raise `AttributeError`), so `if event.persist:` and
  `hasattr(event, "nativeEvent")` both answer **yes** and only the `await` fails. Test the read,
  not the attribute.
- **A typo raises; a `None` is a real answer.** `await event.target.vallue` →
  `EventProxyNotFound`; a property that exists and holds `null` legitimately gives `None`. Do not
  write `or None` fallbacks, and do not silence `EventProxyNotFound` — it almost always means a
  misspelling or a path that does not exist on that element.
- **A read belongs to the moment you await it**, not to the event. `await event.target.value`
  returns what the element holds *now*, so a handler queued behind another one can read an
  already-mutated field. Cached answers replay the first read; `await event.read("target.value",
  refresh=True)` is the only way to re-ask.
- `await event.type` costs **no** round trip — `type` is the one value the client volunteers with
  the handle.
- **On `<form onsubmit>` the target is the `<form>`: `await event.target.value` raises
  `EventProxyNotFound`, and putting that path in a batched `read()` fails the whole batch**
  (`resolve_many` re-raises one failure). `await event.read("target.name")` is fine. Canonical:
  `controls = await event.target.elements` → a plain `list[dict]`, so `c["value"]` /
  `c.get("name")` work; back-references like `c["form"]` arrive as references.
- Read `await event.target.checked` from **`onChange`** — the event a checkbox/radio actually
  fires.
- Blocked members raise `EventProxyAccessError`; the block list (`event-proxy.ts`
  `isBlockedMember`) covers `window`, `document`, `parentNode`, `eval`, `setTimeout`,
  `localStorage`/`sessionStorage`, `location`, `navigator`, every dunder, **and anything matching
  `/^on[a-z]/i`** — so `await event.onPointerDown` is refused too.
- Client offline mid-read → `EventProxyUnavailable`, `EventProxyTimeout`, `EventProxyEvicted`
  (subclasses of `EventProxyError(RuntimeError)`). `await event.is_known` → bool, no round trip.
- Tuning: `REACTPY_EVENT_PROXY_TIMEOUT` (5.0s), `REACTPY_EVENT_PROXY_MAX_DEPTH` (10),
  `REACTPY_EVENT_PROXY_MAX_TIMEOUTS` (3).

## 10. Hooks — signatures

Call only from a component body or another hook, at top level, same order every render.

```python
use_state(initial)                  -> State[current, setter]          # value, set_value fields
use_effect(function, dependencies=...)      # sync only
use_async_effect(function, dependencies=..., shield=False)
use_reducer(reducer, initial_value) -> tuple[state, dispatch]           # plain 2-tuple
create_context(default_value) -> Context;  provider(*children, value=..., key=...)
use_context(context) -> value
use_ref(initial_value) -> Ref[initial_value]      # REQUIRED argument
use_memo(function, dependencies=...) -> value
use_callback(function, dependencies=...) -> function
use_debug_value(message, dependencies=...) -> None
use_connection() -> Connection;  use_scope() -> scope;  use_location() -> Location
```

- **Hook slot cost** (matters for the ordering bug in §11): `use_state`/`use_ref`/`use_memo`/
  `use_callback` = 1 slot; `use_effect`/`use_debug_value`/`use_reducer` = 2;
  `use_async_effect` = 3; `use_context` = **0** (the only hook you may call conditionally).
- `use_state` and `use_reducer` accept a **zero-argument callable** as a lazy initial value; it
  runs once. `use_ref` does **not**: its `initial_value` is evaluated on every render and
  discarded — build once with `x = use_ref(None)` then `if x.current is None: x.current = build()`.
- `use_state` returns the `State` NamedTuple (`value`, `set_value`); `use_reducer` returns a
  plain tuple, so there is no `.value` on it.
- Annotate module-level constants you pass to `use_state`, or Pyright pins the type:
  `EMPTY_SQUARE: str | None = None` before `use_state(EMPTY_SQUARE)`.
- `use_ref()` with no argument raises `TypeError: use_ref() missing 1 required positional
  argument: 'initial_value'`. The low-level `reactpy.utils.Ref()` takes no argument but leaves
  `.current` **unset** → `AttributeError: 'Ref' object has no attribute 'current'`. `Ref` is
  **unhashable** (`__hash__ = None`) and compares **by content** (`.current`).
- `use_context` on a non-context raises `TypeError: <x> is not a Context` or
  `TypeError: <x> has no 'value' kwarg`; passing the *provider* instead of the context is the
  usual cause.
- All three connection hooks raise `RuntimeError: No backend established a connection.` under
  `ReactPyCsr` (there is no server connection at all in a client-side app).

## 11. Hook semantics

- Hooks are **positional slots**, not names (`_life_cycle_hook.py: use_state`). Breaking order:
  - *fewer* hooks than the first render → **silent state corruption**, nothing logged;
  - *more* hooks → `IndexError: list index out of range`, and with debug off the model's `error`
    field is empty, so the region is just blank;
  - a hook inside an event handler or effect body → `RuntimeError: No life cycle hook is
    active. Are you rendering in a layout?`, swallowed into a server-side log line. The UI just
    stops responding.
- Do not call hooks conditionally, in a loop, after an early `return`, or from a plain function.
  Branch on hook *results*, never around hook calls. There is no runtime order check and no lint
  that catches ordering.
- **Dependency comparison is `strictly_equal` (`core/hooks.py`), not React's `Object.is`:**
  1. `type(x) is not type(y)` → changed (`1` vs `1.0`, `True` vs `1`, tuple vs list are changes);
  2. two callables compare **code** only when *both* have a `__qualname__` containing
     `<lambda>`/`<locals>` **and** the same `__qualname__` — so two differently named local
     `def`s with identical bodies are *not* equal, and a local `def` vs. an import is not
     code-compared;
  3. otherwise `==` is tried (the docstring claiming only `int`/`float`/`str`/`bytes` is wrong —
     `hasattr(x, "__eq__")` is true for everything), falling back to `is` if `==` raises.
- Consequences: a dict/list/`@dataclass`/`NamedTuple` rebuilt every render is **not** a
  dependency change (no infinite loop, no need for `use_memo` to stabilize it); a plain class
  instance with no `__eq__` **always** counts as changed and is the shape that actually spins;
  a frozen dataclass or `NamedTuple` with changed fields triggers correctly.
- A `Ref` in a dependency list can never trigger anything: `__eq__` compares `.current` against
  itself, so writes to `.current` are invisible to the comparison. **A latest-value ref must be
  left out of an explicitly written list.**
- **Dependencies argument:**
  | value | meaning |
  | --- | --- |
  | omitted (`...`) | infer from closure cells (locals only) |
  | `[]` | never re-runs / caches forever; body sealed to first render |
  | `[a, b]` | re-runs when a listed value changes; names outside the list go stale |
  | `None` | **re-runs after every render** (not "no dependencies") |
  Inference sees only closure cells: a module-level name is invisible → silently stale. Use an
  explicit list, or `dependencies=None` for "always recompute".
  **Non-function callables** (bound method, `functools.partial`, callable instance) infer `None`
  → silently re-run/recompute every render.
- A missing dependency is **completely silent** — no warning, no log record. A missing dep is a
  correctness bug (values from an older render); an extra dep is a behaviour bug.

## 12. State

- **Setter replaces; it never merges.** `set_user({"name": "x"})` drops the other keys.
  `set_user({**user, "name": "x"})` — but only when `user` is the freshest.
- **In-place mutation is dropped silently.** `items.append(...)`, `user["age"] = 4`,
  `obj.items[0] = x` all compare equal and nothing re-renders. No Immer, no proxy, no error.
- Build new containers. The prescribed translations for lists (`list.insert` is unusable here):
  | mutation | write instead |
  | --- | --- |
  | `items.append(x)` | `[*items, x]` |
  | `items.remove(x)` | `[i for i in items if i is not x]` |
  | `items[i] = x` | `[*items[:i], x, *items[i + 1:]]` |
  | `items.pop(i)` | `[*items[:i], *items[i + 1:]]` |
  | `items.reverse()` | `list(reversed(items))` |
  | `items.sort(key=f)` | `sorted(items, key=f)` |
  and for objects `{**person, "age": 4}`; to drop a key
  `rest = {k: v for k, v in obj.items() if k != "drop"}` (there is no rest-spread in Python).
  Keep identity stable for the items you did not change:
  `[{**a, "seen": True} if a["id"] == id_to_toggle else a for a in artworks]`.
- **Local mutation during this render is fine**, including the `rows = []` / `rows.append(...)`
  children-building loop. The read-only rule covers only state ReactPy handed you and props you
  received — do not be afraid of ordinary list building.
- **`set_items(items.sort())` stores `None`** (in-place `sort`/`reverse`/`append` return `None`) —
  a different failure from the silent drop, and it poisons every later read.
- A shallow copy is not enough: `list(items)` then `next_items[0]["seen"] = True` mutates the
  shared dict and is invisible to the comparison *and* flips the value for every other component
  seeded from the same module-level fixture. Copy every level you change; `copy.deepcopy` is the
  blunt correct fallback (keep state plain dicts/lists/primitives so it stays safe).
- Never derive ids from a module-level counter — it is shared by every connection in the process
  and collides. `next_id = max((i["id"] for i in items), default=-1) + 1`, or `uuid4()` **outside**
  render (never during: keys would change every render).
- **Never store an iterator in state.** `filter()`/`map()`/generators render once and then
  display nothing. Use a comprehension or `list(...)`.
- A shallow copy is not enough: `list(items)` then `next_items[0]["seen"] = True` mutates the
  shared dict and is invisible to the comparison. Build the changed dict explicitly; use
  `copy.deepcopy` for deeply nested structures — and prefer flattening the shape instead.
- **Batching is a latch, per handler.** All setter calls before the first `await` collapse into
  one render (`LifeCycleHook.schedule_render` early-returns once one is scheduled); calls after an
  `await` schedule another. There is no framework-wide batching and no `flushSync`, and no batching
  across separate user events — a first click that disables a form really does stop the second.
- **Updaters compose; plain values do not.** Three `set_count(count + 1)` in one handler end at
  `1` (each evaluates to `set_count(0 + 1)`); three `set_count(lambda c: c + 1)` end at `3`. Use
  the updater form whenever an update depends on current state and two events can land in one
  round trip (double-click, key repeat, latency): events queued before the next render share one
  closure, and the naive form loses an update.
- **Mixing them is a trap:** an updater is applied to the value as of its call, while a plain value
  **replaces and discards earlier updater results**. `set(5)` ≡ `set(lambda n: 5)`. Prefer one
  style per handler, and name the parameter for what it is: `set_enabled(lambda enabled: not enabled)`.
- **An updater rescues only the value it updates.** In `set_seen(lambda previous: [*previous, number])`,
  `previous` is fresh but `number` is frozen from the render that created the closure. Take
  everything from the updater argument, read it before scheduling, or keep it in a `use_ref` box.
- `set_x(...)` writes ReactPy's hook state, **not** the local name `x` — the value a render
  captured stays fixed for the whole life of that render's handler, across `await`s.
- Use the await-flush deliberately: `set_status("submitting")` *before* `await submit_form(...)`
  is what paints the pending/locked state; to avoid the intermediate repaint, await first and set
  once at the end.
- Delayed callbacks are legal and snapshot-bound: `asyncio.get_running_loop().call_later(3, cb)`
  from a handler still sees the creating render's values, and the setter is still valid there.
- Handlers are **not reactive** and do not need `use_callback` to "see fresh values": ReactPy
  keeps one handler per target and looks it up at dispatch time, so a normal click reads
  current state. But a setter called after an `await` is **silently discarded if the component
  unmounted** — the only trace is a debug line
  (`Did not render component with model state ID ... - component already unmounted`).
- Set state in response to a user action from the handler that performed it, not from an effect.
- Keep related values in one dict/tuple only to prevent "forgot the other setter" bugs — it does
  not reduce renders. Mutually exclusive booleans should be one `status` string.
- Store the **id**, derive the object during render (`next(i for i in items if i["id"] == id)`).
  Never store a derived object in state or in a dependency list.
- Derived values are computed, not stored: `total = sum(...)` in the body. `use_memo` caches a
  value (it never caches a render), and an Effect that sets state it depends on **never
  settles** — measured hundreds of renders, no error. The functional updater is what breaks the cycle.
- Reset state with a `key` on the component, not with an Effect.
- ReactPy's render-phase "adjust state during render" trick **does not work**: the stale patch
  reaches the browser and is then clobbered. Derive the value instead.
- Read the newest value inside a long-lived loop from a `use_ref` box written during render.
- There is no render profiler: count renders with a `use_ref(0)` counter incremented in the body.
- **Inputs:** an *uncontrolled* input simply omits `value` (`html.input({"placeholder": ...})`).
  The untouched subtree then produces an empty patch, so typed text, cursor position, and the DOM
  node itself survive a parent re-render. Add `"value"` only when it is genuinely derived from
  state, and always with the matching `"onChange"`; a `value` with no `onChange` is a frozen box.
  Keep a controlled input's state a **`str`** — the client only reconciles a string `value` onto
  the field. Express availability as data: `{"disabled": status in {"empty", "submitting"}}`.
- Store **errors as strings** (`set_error(str(exc))`), never exception objects — they are not
  JSON-serializable.
- Lazy initial value: `use_state(lambda: json.loads(big_blob))`. Passing the *result* re-runs the
  expression on every render (Python evaluates the argument before `use_state` sees it) and then
  throws it away. Same for `use_reducer`; `use_ref` has no such option.

## 13. Effects

**Which hook, and how it is called**

- `use_effect(function, dependencies=...)` is **sync only**:
  `TypeError: \`use_effect\` does not support async functions. Use \`use_async_effect\` instead.`
  (backticks are in the real message). It lands in the model's `error` field only under
  `REACTPY_DEBUG`; otherwise the region is blank and the traceback is server-side.
- A sync effect body runs on the connection's own event loop and **blocks it** — `time.sleep(0.4)`
  in an effect made the next click take 0.40 s and queued every other handler behind it. Blocking
  work belongs in `use_async_effect` with `asyncio.to_thread`.
- `use_async_effect(function, dependencies=..., shield=False)` does **not** validate `async def`;
  a plain `def` fails inside the task (`a coroutine was expected`) with only a server-log trace.
- The effect takes **no arguments**; its cleanup takes **no arguments**.
- A bare `@use_effect` / `@use_async_effect` decorator **cannot infer dependencies** — at call
  time the function does not exist yet, so deps become `None` and the effect re-runs **after
  every render**, parking an extra task each time. The decorator form is only correct as
  `@use_effect(dependencies=[...])`.

**Timing and clean-up**

- Effects are scheduled at the *end of the render*, not after the browser paints, and they never
  delay the render (measured: `layout.render()` returned in 0.000 s while an async effect slept
  0.5 s). Do not assume the user can see what an effect is doing.
- A clean-up returned by a completing coroutine runs **on the successor's task, just before the
  successor's setup**, so teardown sees the *old* captured values; unmount runs the last clean-up
  exactly once. A never-completing `while True:` loop must tear down in
  `except asyncio.CancelledError: handle.close(); raise` — always re-raise.
- Old **sync** effect tasks are never cancelled: they park on a stop event and are reaped at
  unmount — one parked task per re-synchronization.
- Two **async** runs can be alive at once (cancellation lands at the next `await`) and a
  superseded run can still write state. Guard the write with a ref written during render
  (`if name == expected_name.current: set_loaded(...)`), and store each response together with the
  input that produced it, deriving on read.
- `shield=True` keeps work alive through unmount — a leak unless you add your own timeout.
- Never own background work with a task in a `use_ref`: it is never cancelled and outlives the
  component. `use_async_effect` owns tasks; refs hold plain shared values.

**Failures**

- An effect body that raises is **not** logged at mount — the single `ERROR Error in effect`
  record appears when the component **unmounts**, where parked tasks are finally awaited. Silent
  log + fine-looking page is the normal symptom. Catch it yourself and put it in state
  (`try: set_metrics(fetch()) except Exception as error: set_error(str(error))`), and in tests
  assert the *external* world, not the render.
- An effect that sets state it also depends on **never settles** (measured: 86+ renders, no
  error). Read what it awaits, what it depends on, what it sets. Deleting the dependency to
  silence it, or adding `if already_ran.current: return`, just hides a wrong dep list.
- `ValueError: Cell is empty` during render → the effect is registered **above** the local it
  reads (inference reads closure cells at call time). State first, effects after.
- Gate an effect with a flag **inside the body and in the deps**
  (`use_effect(effect, dependencies=[topic, enabled])` + `if not enabled: return None`). Never
  wrap the hook call in `if`, and never leave the flag out of the list.

**What actually belongs in one**

- Legitimate when the source of truth lives outside ReactPy and the state exists purely to trigger
  a render: subscriptions, polling, sockets, external stores — always with a clean-up that returns
  the world to zero. Nobody should be able to tell whether the effect ran once or ran
  setup→cleanup→setup.
- Subscribe *inside* the effect and define the callback there too; a callback defined in the
  component body leaves the subscription holding the first version of it.
- Keep separate synchronizations in separate `use_effect` calls — merging them means one
  dependency change tears down the other's subscription.
- Declaration order inside one component is the only ordering safe to rely on; never require a
  parent's effect to have run before a child's.
- **An effect runs once per connection, and one process serves many connections.** Process-level
  setup (`configure_logging()`, pools, caches) belongs at module level or in the ASGI app's
  startup, not behind `dependencies=[]`. Never guard it with `my_component.started = True` — the
  function object is module-scope, so the first visitor flips it for everyone.
- **Not** effects: deriving a value (compute in render), caching (`use_memo`), resetting on prop
  change (`key=`), work triggered by a user action (the handler), notifying a parent (a callback
  prop called from the child's handler), form submission (the handler — an effect re-runs on
  remount and can send twice). For fetching, ReactPy is already on the server: fetch in the
  parent's render or at startup and pass the result down; keep an effect only for data that
  depends on something only the connection knows (e.g. `use_location`).
- ReactPy has **no StrictMode and no double-invoke**: the restart-safety check React gives you
  for free is one you run yourself (render → unmount → remount → assert the external system).

## 14. Refs (no DOM)

- `use_ref(initial_value)` is a server-side mutable box built on `use_state` machinery — it
  **reserves a hook slot**. There is **no** `<div ref=...>` equivalent, no `forwardRef`, no
  `useImperativeHandle`, no `flushSync`.
- Rule of thumb: a value used for rendering → `use_state`; a value only handlers or long-lived
  coroutines need, whose change must not re-render → `use_ref`. Refs are exempt from the
  mutation rules of state — mutating what a ref holds is fine precisely because it never renders.
- `use_ref(initial_value)` requires the argument
  (`TypeError: use_ref() missing 1 required positional argument: 'initial_value'`) and **re-evaluates
  it every render**, discarding the result. Build once with `box = use_ref(None)` +
  `if box.current is None: box.current = build()`. Unlike `use_state`, there is no lazy initializer.
- The low-level `reactpy.utils.Ref()` takes no argument but leaves `.current` **unset** →
  `AttributeError: 'Ref' object has no attribute 'current'`, `repr` → `Ref(<undefined>)`. `Ref` is
  **unhashable** (`__hash__ = None`) and compares **by content**, so two separate `Ref(0)` boxes
  are equal and neither can be a dict key.
- `use_ref(x)` is **not** "the current x" — it keeps the first box forever. The latest-value idiom
  is a render-time write: `latest = use_ref(x)` then `latest.current = x` in the body, read by
  long-lived effects as `latest.current` (re-read each pass, don't bind it to a local).
- Do not read or write `ref.current` during render, except the create-once guard and the
  latest-value write above. Assign in the handler that produces the value.
- `html.div({"ref": {"current": None}}, ...)` is forwarded verbatim as an ordinary attribute and
  silently does nothing (preact writes into its own decoded copy) — a "focus the input" button
  built this way focuses nothing. `{"ref": "my_ref"}` throws in the **browser**:
  `TypeError: Cannot create property 'current' on string 'my_ref'`, nothing in the server log.
  `{"ref": <Ref instance>}` is not callable, so it stays an attribute and dies at encode:
  `TypeError: Object of type Ref is not JSON serializable`.
- Declarative substitutes, in order of preference: `{"autoFocus": True}` (**mount only** —
  re-keying the element does *not* re-fire it, verified), `{"hidden": not show}`,
  `{"value": text}`, `{"disabled": not ready}`, `style`. For the imperative remainder (focus on
  click, scroll into view) use an inline-JS handler reaching an element by `id`:
  `{"onClick": "document.getElementById('search').focus()"}` — interpolate only ids you wrote.
- Never mutate DOM ReactPy rendered (an inline-JS `remove()` on an owned node silently breaks the
  next patch). Remove nodes by changing state. An element ReactPy renders empty and never writes
  children to is yours to fill from inline JS.
- Rendering a box instead of its value is silent: `html.p(my_ref)` prints `Ref(0)`.

## 15. Custom hooks

- Legal and ordinary: a function that calls other hooks. Nothing to register or export.
  Name it `use_snake_case` (the linter's pattern is `^_*use_\w+$`) and define it at module
  level — a nested `use_*` is a closure (REACTPY100).
- Add `use_` **only** when the function calls hooks; prefixing `format_rows()` makes the linter
  police an ordinary function as a hook.
- They share **logic, never state**: state is per call site, in call order. Two calls in one
  component = two independent boxes. Not a state container (use props or context).
- Never list a callback you were handed as an effect dependency: it freezes the effect on the
  first render forever, silently. Keep it in a ref refreshed during render and leave it out of
  the list. Listing a handler does not make it fresher.
- Do not branch to disable a hook (`if polling: use_async_effect(...)`) — keep the call and
  branch inside the hook body.
- Keep them concrete (`use_polling(topic, on_result)`) rather than generic
  (`use_async(fetcher, deps)`), and never a render bailout (there is no `memo`).

## 16. Context

```python
ThemeContext = create_context("light")        # module level, PascalCase by docs convention
from reactpy.types import Context             # for annotations: Context[str] = create_context("light")
ThemeContext(*children, value="dark")         # provider; renders a nameless fragment
use_context(ThemeContext)                     # in a CONSUMER, never in the provider's own body
```

- Matched **by identity**: create once at module level and import it. Two `create_context` calls
  with the same default are two unrelated contexts.
- **A component cannot read the context it provides.** Arguments evaluate during the parent's
  render, before the provider is entered, so the read returns the default. Read it in a child.
- Keep the provider in the tree permanently — un-wrapping is never a way to "unset" a value. What
  shifts position gets unmounted and loses its state; whatever happens to stay mounted at the same
  position **keeps the value it inherited**, because a component's context mapping is merged and
  nothing prunes it. To force a reset, change the child's `key`. Express "not provided" as the
  default value, not as an absent wrapper.
- Context is not reactive and not a perf feature: when the provider re-renders, everything below
  re-renders whether the value is new, equal, or identical. Cost is governed by provider
  *placement*. Two sibling subtrees under one provider still get independent state.
- Context carries values **down**. For shared mutable state, put `use_state`/`use_reducer` in a
  common ancestor and pass the setter/`dispatch` down alongside the value; the usual shape is
  one context holding `(state, dispatch)` plus an accessor hook.
- The provider instance is identified by its `render` function, so a new closure (nested
  definition, or the decorated function passed undecorated) never registers as the provider, and
  consumers silently render the `create_context` default rather than raising. Pass the decorated
  function and define it at module level.
- Choose a default the component can handle: it is also what a unit-test render sees.
- Use context only for values that genuinely travel through layers; one level deep should stay a prop.

## 17. Reducers

```python
def tasks_reducer(state, action):
    kind = action["type"]
    if kind == "add":
        return {"tasks": [*state["tasks"], action["task"]]}
    raise ValueError(f"unknown action type {kind!r}")     # never fall through silently

state, dispatch = use_reducer(tasks_reducer, INITIAL_STATE)
dispatch({"type": "add", "task": task})
```

- `use_reducer(reducer, initial_value)` takes **exactly two arguments** — no React-style third
  "init function" (a zero-arg callable as `initial_value` is still honoured).
- `dispatch` is **eager**: it runs the reducer synchronously against the latest committed value.
  Do not read `state` immediately after `dispatch`. Do not dispatch during render.
- Actions are opaque to ReactPy — `{"type": ...}` dicts are convention. One action per user
  interaction; actions describe what happened.
- The reducer must be a module-level pure function of `(state, action)` only.
- Once the state grows past a couple of branches, make it a `@dataclass(frozen=True)` and build
  next state with `dataclasses.replace(...)` — a mutation then raises `FrozenInstanceError` at
  the offending line instead of silently doing nothing. The raise surfaces on the `reactpy.core.layout`
  logger (`Failed to execute event handler ...`); the component stays mounted.
- `use_state` and `use_reducer` are equally cheap (both compare with `==`, both skip the render,
  neither bails out of rendering). Reach for a reducer after a real wrong-update bug, not by default.

## 18. Connection, scope, location

- `use_connection() -> Connection(scope, location, carrier, carrier_info)`; `carrier` is
  backend-specific (a Starlette `Request` under `ReactPyMiddleware`, `None` under `ReactPy`);
  `carrier_info` is always `None`. `Connection` has **no `send`/`deliver`/`close`** — you cannot
  write to the socket.
- `scope` and `location` are **live objects, not copies**. Treat both as read-only. One
  `Connection` per browser tab, not per render.
- `scope["headers"]` is a list of `(bytes, bytes)` pairs, **lower-cased** — match `b"user-agent"`
  and `.decode()`; comparing to a `str` silently yields `None`. `scope["client"]` may be absent
  or `None` behind a proxy → use `.get()`. Other keys (`path`, `method`, `query_string`,
  `root_path`, `asgi`, `extensions`) are server-specific.
- `use_location()` returns `Location(path, query_string)`. `query_string` is the page's own
  `window.location.search`, **leading `?` included** (`"?tab=2"`), and `""` when there is no query
  — do not assume either form. Some docs examples show it without the `?`; the client sends it
  verbatim, so handle both. It is **untrusted browser input** carried as websocket URL parameters
  and never validated against your routes — match it, never interpolate it into an `href`, a path,
  or a query you then fetch.
- Reading request data is *not* the same as "there was an HTTP request": the scope belongs to
  the long-lived websocket. For pre-connection decisions, use ASGI middleware in front.
- Unit-test idiom:
  ```python
  from reactpy.core.hooks import ConnectionContext
  from reactpy.core.layout import Layout
  from reactpy.types import Connection, Location
  conn = Connection(scope={"headers": [(b"user-agent", b"test")]},
                    location=Location(path="/x", query_string=""), carrier=None)
  async with Layout(ConnectionContext(page(), value=conn)) as layout:
      model = (await layout.render())["model"]
  ```

## 19. Server ↔ client data flow

Two channels only: the model down (`layout-update`), events up (`layout-event`).

- **There is no server→client push of arbitrary messages.** "Pushing" = `use_async_effect` +
  a state setter (loop with `while True:`, `except asyncio.CancelledError: raise`; `shield=True`
  to survive unmount). Prefer awaiting a queue over polling.
- A hand-written frame on the socket is dropped with
  `[ReactPy] Received message without handler` in the browser console. Do not build on it.
- **File uploads send metadata only, never bytes.** An entire `await event.target.files` entry for
  a 12-byte file is `[{"name", "lastModified", "lastModifiedDate", "webkitRelativePath", "size",
  "type"}]` — the client's own-property walk skips functions, so `File.text()`/`arrayBuffer()`
  never come across. There is no `FormData` and no chunked-upload path. Working recipe (every part
  load-bearing): an `onChange` **string** handler doing
  `event.target.files[0].text().then(t => document.getElementById('payload').value = t)`, a
  **separate submit button** (the promise races a direct send, and an Enter-key submit is a second
  event), and a hidden input with both `id` (for the JS) and `name` (for the form walk).
  `event.preventDefault()` must appear literally in the handler body. Binary = `arrayBuffer()` +
  base64; for large files, post to a normal HTTP endpoint and pass the id through state.
- `submit` on a form: `await event.target` (or `.elements`) is iterable → a list of plain
  control dicts.
- A **method call is the one door that ships arguments down**: `await event.getCoalescedEvents()`
  sends your args as JSON. Values normalize on the way up: `Date` → ISO-8601 string, `Error` →
  `{name, message, stack}`, `RegExp` → string, `bigint` → number or decimal string.
- A dispatch for a target that is gone is logged, not raised:
  `Ignored event - handler '<target>' does not exist or its component unmounted`
  (and `Failed to execute event handler ...` when the handler itself raises). Both are
  **server-side only**.
- Blocking or CPU-bound work: `await asyncio.to_thread(...)`. Calling a setter from a raw
  `threading.Thread` fails with `RuntimeError: no running event loop` + "coroutine ... was never
  awaited" and nothing in the browser; capture the loop and use `loop.call_soon_threadsafe(setter, value)`.
- Client-only APIs (localStorage, clipboard, computed style, DOM nodes) are unreachable from
  Python. Options: compute server-side, copy the value into a form field, run one inline-JS call,
  or render it yourself (`reactpy.widgets.image`, server-built `<svg>`).
- Never store state on the component function object (`my_component.started = True`) — it is
  shared by every connection in the process.

## 20. Rendering, lifecycle, errors

- ReactPy calls your component on mount, on its own state change, and **whenever its parent
  renders**. There is no memo bailout anywhere; render counts are not yours to predict.
- **Purity is load-bearing on a server.** A module-level `dict`/`list` written during a render is
  shared by *every connection in the process* and survives reconnects — measured: three visitors,
  one growing cart, no error. Local mutation of objects you created during this render is fine.
- No I/O, clock, `random`, env, printing, task/thread/timer creation in a component body.
  `print()` in a component or handler lands in the **terminal running the ASGI server** — there
  is no browser console to open.
- A raising component does **not** kill the socket: the client receives
  `{"tagName": "", "error": "<message>"}` and prints it in place of the component — but only with
  `REACTPY_DEBUG=1`. With debug off `error` is `""` and the component silently disappears.
- Handler/effect errors are **server-side only**: `Failed to execute event handler ...`,
  `Error in effect`. Dead button + clean console ⇒ read the server log.
- Events for one target run **sequentially** (a queued event sees writes from the earlier one,
  including across `await`); different targets run concurrently.
- Remounting a subtree whose handler dict has an **explicit** `target` re-registers the same
  target and raises `KeyError: <target>` on unmount, leaving stale handlers. Omit `target` and
  let ReactPy generate it (per element, via `key_path`).
- `Layout.deliver()` is for custom backends; app code dispatches nothing by hand.
- Patches **replace** subtrees and never merge; wrappers with `"tagName": ""` surround
  components — never index the model by position.
- Nothing runs during a render for un-mounted components, and rendering may be discarded or
  restarted; there is no ordering guarantee between components.
- Unmount/cleanup does not run while `Layout.render()` blocks with nothing pending.

## 21. Executors and deployment

All three live in `reactpy.executors.asgi`, all accept `**settings`, all are instantiated once
at module level and handed to an ASGI server.

**`**settings`** are the `ReactPyConfig` keys — the `REACTPY_*` names, lowercased, no prefix:
`path_prefix`, `web_modules_dir`, `reconnect_interval`, `reconnect_max_interval`,
`reconnect_max_retries`, `reconnect_backoff_multiplier`, `async_rendering`, `debug`,
`max_queue_size`, `event_proxy_timeout`, `event_proxy_max_depth`, `event_proxy_max_timeouts`
(`tests_default_timeout` is env-only; the kwarg raises `TypeError` because that Option is not
mutable). An unknown key raises `ValueError: Unknown ReactPy setting "x".`
**These are process-wide globals**, not per-app config: each is written to the matching
`reactpy.config.REACTPY_*` option, so the last executor constructed wins for the whole process.

| | `ReactPy` | `ReactPyMiddleware` | `ReactPyCsr` |
| --- | --- | --- | --- |
| Where Python runs | server | server | **browser** (PyScript/Pyodide) |
| Root given as | the `@component` **function** | **dotted-path strings** | a **file path** + `root_name` |
| Websocket | yes | yes | no |
| Component source visible to users | no | no | **yes** |
| Serves HTML | yes (empty shell) | **never** | yes |

**`ReactPy(root_component, *, http_headers, html_head, prepend_body, html_lang, pyscript_setup, pyscript_options, **settings)`**
- Standalone single-page app. **It is not SSR of your component**: the index has an empty
  `<div id="app">` and all markup arrives over the websocket, so `curl` and search engines see
  nothing. Only `html_head` and `prepend_body` are server-rendered.
- `html_head` **must** be built with `html.head(...)` → otherwise, at request time (500, not
  import time): ``ValueError: Head element must be constructed with `html.head`.``
- `prepend_body` defaults to `html.noscript("Enable JavaScript to view this site.")`; it is
  rendered with `reactpy_to_string`, so it may not use hooks.
- `@my_app.route(path, type="http"|"websocket")` and `my_app.lifespan(app)` add your own routes
  (path is a regex, `^`/`$` auto-added; the app may be a callable or a dotted-path string).
- `pyscript_setup=True` loads PyScript alongside server-rendered components for mixed setups.
- Serves `{path_prefix}` (index + dispatcher), `{path_prefix}static/` (client bundle),
  `{path_prefix}modules/` (web modules). Everything else is yours.

**`ReactPyMiddleware(app, root_components, **settings)`**
- `root_components` is a required iterable of **dotted paths** (`["main.counter"]`), resolved via
  the Python import system from the server's working directory. Failures at construction:
  `ImportError: ReactPy failed to import "main"` / `AttributeError: ReactPy failed to import
  "counter" from "main"`; no dot at all → `ValueError`.
- It **never serves HTML**: registering a component does not create a page. Emit the mount
  markup yourself with `server_side_component_html(element_id="app", class_="",
  component_path="main.counter/")` — **the trailing slash is required** (the websocket route is
  `^{path_prefix}(?P<dotted_path>[a-zA-Z0-9_.]+)/$`). Without it: `Unexpected response code` +
  `[ReactPy] Failed to connect!` and an empty div.
- Mounting by hand (`<script type="module">` + `import { mountReactPy } from "{prefix}static/index.js"`):
  `pathPrefix` must start **and** end with `/`; `componentPath` carries a trailing slash under
  the middleware and must be **omitted** under `ReactPy`. There is no `unmountReactPy` —
  removing the node leaves the socket and layout alive; only navigation tears down.
- Unregistered path → `Attempting to use an unregistered root component <path>.`
- `@my_app.route(...)` does **not** exist on the middleware (every route is your app's).
- Validation: `path_prefix` must start and end with `/` →
  ``Invalid `path_prefix` of "/some-app". URL path must end with a forward slash.``;
  a non-existent `web_modules_dir` → `ValueError: Web modules directory "..." does not exist.`

**`ReactPyCsr(*file_paths, extra_py, extra_js, pyscript_config, root_name="root", initial, ...)`**
- Runs your components in the browser. **The files you pass are inlined into the HTML — they are
  published.** No secrets, DB access, or privileged calls in those files.
- The root component must be named `root` unless you pass `root_name=`; no paths →
  `ValueError: At least one component file path must be provided.`
- Files are read once and cached per process (`functools.cache`) — restart the server after
  editing. Comments and inner docstrings are stripped by `minify_python` (module docstring kept).
- `extra_py` packages must install under Pyodide; `extra_js` is `{url: export_name}`, reachable
  as `pyscript.js_modules.<name>`; `pyscript_config` replaces the PyScript config lists.
- Cold start downloads a CPython runtime — that is what `initial=` is for. Most settings are inert.

**Multi-worker deployment:** `REACTPY_WEB_MODULES_DIR` defaults to a per-process temp dir, so a
module registered by one worker 404s for another. Pin it (`web_modules_dir=Path(...)`, or the
env var) to one shared path. The directory must **already exist** —
`ValueError: Web modules directory "..." does not exist.` — and registration copies the file in at
import time. Treat it as a black box; read `config.REACTPY_WEB_MODULES_DIR.current` only *after*
constructing the executor (`**settings` repoints it).

**Rolling your own ASGI wiring** (a route inside an existing app, rather than one of the three
executors) needs two primitives: `reactpy.core.layout.Layout` and
`reactpy.core.serve.serve_layout(layout, send, recv)` — you supply two coroutines. Wrap the root:
`Layout(ConnectionContext(my_component(), value=Connection(scope=scope,
location=Location(path=..., query_string=...), carrier=None)))`, or the connection hooks raise
`RuntimeError: No backend established a connection.` on a healthy socket. `serve_layout` binds
your `send` as the proxy sender and `Layout.deliver` recognises `event-proxy-response` itself, so
**pumping every received frame into `deliver` gives live event reads for free** — a backend that
filters frames first (matching `"layout-event"`, like the middleware) must route the responses
itself, or every `await` on an event stalls until timeout. `deliver` is fire-and-forget
(`start_soon`), so a slow handler never blocks the next event. The usual traps: skip
`websocket.connect` and you `orjson.loads()` a dict with no `"text"` key (socket opens then
closes, `[ReactPy] Disconnected!`, endless reconnect); `recv()` must never return `None`; build
**one `Layout` per connection** inside the handler, never cached by component name; send **text**
frames (the client never sets `binaryType`, so a binary frame dies with
`SyntaxError: ... "[object Blob]" is not valid JSON`); under `async with` the handshake is already
done — don't send `websocket.accept`. Routes you must serve yourself: `{path_prefix}static/` (the
client bundle, from `Path(reactpy.__file__).parent / "static"` — keep it a child of your mount
prefix or the chunks 404 while `index.js` loads), `{path_prefix}modules/`, and
`{path_prefix}<name>/` for the websocket. `servestatic` and `asgi_tools` (both in the `asgi`
extra) cover the static and websocket pieces.

## 22. Jinja templates (Flask / Django / Starlette)

```python
from reactpy.templatetags import ReactPyJinja      # a jinja2-simple-tags StandaloneTag
env = Environment(loader=FileSystemLoader("templates"), extensions=[ReactPyJinja], autoescape=True)
```

Register **before** any template using the tags is compiled, or:
`TemplateSyntaxError: Encountered unknown tag 'component'.` Three tags, registered together:

- `{% component "my_app.pages.counter" %}` — mount markup for a **server** component; the path
  must match a `root_components` entry **character for character** (a wrong path is not checked:
  an empty element forever). Kwargs must follow a comma: `{% component "m.f", class="badge" %}`.
  Bad kwarg → `ValueError: Unexpected keyword arguments: id, style`; missing path →
  `TypeError: component() missing 1 required positional argument: 'dotted_path'`.
- `{% pyscript_setup %}` — once per page, in `<head>` (`extra_py` positional/repeatable,
  `extra_js='{"./my.js":"mylib"}'`, `config` JSON).
- `{% pyscript_component "components/counter.py" initial="Loading..." root="root" %}` — paths are
  relative to the process CWD; the file is inlined, never fetched. Missing file →
  `FileNotFoundError`; no root function → `ValueError: Could not find the root component function
  'root' in your PyScript file(s).` Both surface as a 500 at render time.
  Component source is inlined and minified (inner docstrings stripped, module docstring kept);
  debug mode changes nothing here.

## 23. JavaScript / npm components

Current API is `reactpy.reactjs`; `reactpy.web.module_from_url/_file/_string` and
`reactpy.web.export` are **deprecated** (DeprecationWarning → use the `component_from_*` forms).

```python
from reactpy.reactjs import component_from_npm, component_from_url, component_from_file, import_reactjs

Badge, Spinner = component_from_npm("baseui", ["Badge", "Spinner"], version="latest")
html_head=html.head(import_reactjs())        # REQUIRED in the page <head> for npm components
```

- Signatures: `component_from_npm(package, import_names, resolve_imports=False,
  resolve_imports_depth=5, version="latest", cdn="https://esm.sh/v135", bundle=True,
  fallback=None, unmount_before_update=False, allow_children=True)`;
  `component_from_url(url, import_names, ...)`;
  `component_from_file(file, import_names, ..., name="", symlink=False, ...)`.
  A string `import_names` returns one `VdomConstructor`, a list returns a list.
- `import_reactjs(framework="preact"|"react"|None, version=None, use_local=False)` returns an
  `html.script` with `{"type": "importmap", "id": "reactpy-importmap"}`. ReactPy injects its own
  map only if no element with **that id** exists (the id, not the content).
  `use_local=True` with `framework`/`version` → `ValueError: use_local cannot be used with
  framework or version`.
- They render `{"tagName": "Badge", "importSource": {"source": ..., "sourceType": "NAME"|"URL",
  "fallback": ..., "unmountBeforeUpdate": false}}`. `"NAME"` → the browser imports
  `{path_prefix}modules/<source>`; `"URL"` → imports the URL directly. A component with an
  `importSource` is not a `@component` and cannot be called with `key=`.
- `resolve_imports=True` (default **`False` for all four** `component_from_*`) makes a bad export
  fail in Python at registration — `ValueError: 'badge.js' does not contain 'Nope'`; with the
  default you only get a browser-console line
  (`Module from source {...} does not export Nope`) and nothing renders. Turn it on in dev.
  Nested exports are addressable by dotted name (`"My.Nested.Component"`).
- `allow_children=False` → `TypeError: 'Badge' nodes cannot have children.`
- `fallback=` is the element shown while the module loads — without it a slow module looks broken.
  `unmount_before_update=True` forces a full DOM rebuild per update.
  `bundle=False` is the escape hatch for packages whose sub-paths esm.sh bundling breaks. The
  `cdn` default is `https://esm.sh/v135` (a docstring says `https://esm.sh` — trust the signature).
- A JS module may export `bind` (`bind(node, config)` → `{create, render, unmount}`). Without it
  ReactPy infers one and logs at `console.debug` **without** a `[ReactPy]` prefix — a missing or
  misnamed `bind` is invisible. Present but wrong-shaped → `console.error: <source> returned an
  impropper binding` (that misspelling ships) while Python stays happy. Ship it explicitly.
  Nested access (`module.Component`) also works through `Vdom.__getattr__` when an
  `import_source` is set.
- Your own import map must carry `id="reactpy-importmap"`, or ReactPy injects a second one and the
  browser conflicts on the `"react"` rule. With no map at all the client silently falls back to
  bundled preact at `console.debug`.
- The deprecated `reactpy.web` forms use the **old** kwarg names `resolve_exports` /
  `resolve_exports_depth` (vs `resolve_imports` / `resolve_imports_depth`), and warn verbatim:
  `module_from_url is deprecated, use component_from_url instead`, …,
  `export is deprecated, use component_from_* functions instead`.

## 24. Configuration and debugging

`reactpy.config.REACTPY_*` are `Option` objects; read/assign with `.current`
(`config.REACTPY_DEBUG.current = True`). The **environment variable is read when
`reactpy.config` is first imported**, so `os.environ["REACTPY_DEBUG"] = "1"` afterwards does
nothing — start with `REACTPY_DEBUG=1 uvicorn main:my_app`.

| Variable | Default | Notes |
| --- | --- | --- |
| `REACTPY_DEBUG` | `False` | master switch; enables the two checks below, fills the model's `error` text, enables key warnings |
| `REACTPY_CHECK_VDOM_SPEC` | parented to DEBUG | VDOM schema validation |
| `REACTPY_CHECK_JSON_ATTRS` | parented to DEBUG | JSON-serializability of attributes |
| `REACTPY_WEB_MODULES_DIR` | per-process temp dir | pin it under multiple workers |
| `REACTPY_PATH_PREFIX` | `/reactpy/` | must start and end with `/` |
| `REACTPY_ASYNC_RENDERING` | `True` | |
| `REACTPY_MAX_QUEUE_SIZE` | `1000` | |
| `REACTPY_RECONNECT_INTERVAL` / `_MAX_INTERVAL` / `_MAX_RETRIES` / `_BACKOFF_MULTIPLIER` | `750` / `60000` / `150` / `1.25` | client websocket |
| `REACTPY_EVENT_PROXY_TIMEOUT` / `_MAX_DEPTH` / `_MAX_TIMEOUTS` | `5.0` / `10` / `3` | live event reads |
| `REACTPY_TESTS_DEFAULT_TIMEOUT` | `15.0` | not mutable — env var only |

- `use_debug_value(message, dependencies=...)` logs at `DEBUG` on the `reactpy.core.hooks` logger,
  and only under `REACTPY_DEBUG` (a warnings-only logging config hides it entirely). `message` may
  be a value or a zero-arg callable. Its comparison is plain `!=` (unique among hooks) and is
  **not guarded**, so a raising `__eq__` breaks the render — keep messages to plain data. The
  comparison runs every render whether or not anything is logged, and the first render always
  logs. Log line: `"<component repr> <message>"`. "Logs every render" means the message is a
  timestamp, `id(...)`, or a freshly built identity-compared object; "stopped logging" → confirm
  with a temporary `dependencies=None`.
- Symptom → cause:
  | Symptom | Cause |
  | --- | --- |
  | `<function name at 0x...>` on the page | component passed, not called |
  | dict/tuple repr on the page | component returned a list/tuple, a stray comma, or a stray `*` |
  | list renders empty | a helper forgot `return` |
  | button dead, console clean | handler raised on the server (or was sync/lambda/wrong arity) |
  | component vanishes | it raised, with `REACTPY_DEBUG` off |
  | `ValueError: Cell is empty` in the model | effect registered above the state it reads |
  | update silently does nothing | in-place mutation, or a new object that compares equal |
  | state values swapped between rows | hook order changed between renders |
  | state attached to the wrong row | missing or index-based keys |
  | form submits anyway / event still bubbles | bytecode detection missed your `preventDefault()` |
  | effect never runs | wrong `dependencies` (page fine, log clean forever) |
  | effect body raised | nothing logged until the component unmounts |
  | empty `<div id="app">` in `curl` | expected — content arrives over the websocket |
  | `403`/`Failed to connect!` on the socket | wrong `componentPath`/`path_prefix` (never retried) |
  | two users share a counter/cart | module-level state, or a module-level element being mutated |
  | effect never stops | it sets state it also depends on |
  | ReactPy-internal `NotImplementedError` mentioning `unsupported request of type` | stray `/` in `componentPath` under standalone `ReactPy` |

## 25. Testing your app

Most tests need no browser — a pure component is an ordinary function:

```python
import asyncio
from reactpy.core.layout import Layout

def render_model(component_instance):
    async def go():
        async with Layout(component_instance) as layout:
            return (await layout.render())["model"]
    return asyncio.run(go())

render_model(my_button())        # a call, not the function
```

- `Layout(root)` takes a **component instance** (or a context/provider) — passing the undecorated
  function raises `TypeError: Expected a ReactPy component, not <class 'function'>`.
- Fresh component instance and fresh event loop per call; render twice and compare the models to
  catch impurity (there is no StrictMode to do it for you).
- `Layout.render()` **blocks** when nothing is pending → wrap in `asyncio.wait_for` or drive
  events with `await layout.deliver(...)`.
- Under the default `REACTPY_ASYNC_RENDERING=True` a **sync** effect body has already run by the
  time `await layout.render()` returns — no extra awaits needed. Insert `await asyncio.sleep(0)`
  only if you have turned async rendering off, or to let an *async* effect's task advance.
- To test re-synchronization, drive the layout: render, `await layout.deliver(...)`, render
  again, and assert the *external* side effects (the subscription count, the log of connects and
  closes) rather than the model.
- Unmounted component + queued event = cleanup never runs.
- Inject a connection with `ConnectionContext` (§18) instead of a real server.
- Browser-level tests: `from reactpy.testing import DisplayFixture, poll` (needs
  `reactpy[testing]`; `display.page` is a Playwright page).

## 26. Tooling and ecosystem

- The docs' toolchain is **Ruff** (lint + format) and **Pyright**.
- `reactpy-flake8` (separate package, v0.7, **not** installed with reactpy and not a dependency)
  implements eslint-plugin-react-hooks-style checks: `REACTPY100` hook defined as a closure,
  `REACTPY101` used outside a component/hook, `REACTPY102` used inside `if`/`try`/`for`/`while`/
  `match`, `REACTPY103` used after an early return (`hook 'use_state' used on line N`). It matches
  **names** (hooks `^_*use_\w+$`, components = decorated with `component`), so renaming the
  decorator disables it, and a camelCase `useForm` degrades to a less useful message. The
  dependency half is opt-in (`exhaustive_hook_deps=True`) and narrow: `REACTPY200` a dependency
  written as `obj.attr`, `REACTPY201` the dependencies value is not a literal list/tuple/`None`,
  `REACTPY202` an **inline lambda** effect missing a name assigned at the top of the component
  body — it stays silent for a named `def` body and for the decorator form, and it keys off a
  keyword ReactPy does not use (`args=` rather than `dependencies=`), so it false-positives on
  correct code. Do not trust the `REACTPY20x` family; nothing at all checks hook *order*, and
  nothing warns about a missing dependency. Runtime has no guard either — you are the lint.
- First-party packages that are **not** part of `reactpy`: `reactpy-router` (SPA URL routing —
  don't hand-roll a router) and `reactpy-django`. `reactpy-jupyter` and `reactpy-dash` exist but
  are documented as broken; don't promise them.
- `reactpy.widgets` is small: `image(format, value="", attributes=None)` (base64 data-URI
  `<img>`; `"svg"` → `image/svg+xml`) and
  `use_linked_inputs(attributes, on_change=..., cast=..., initial_value="", ignore_empty=True)`
  (a list of `html.input` elements sharing one value; put a `"key"` in each attrs dict if the
  count varies).
- HTML conversion — read the caveats before shipping output from either direction
  (`reactpy.utils`):
  - `reactpy_to_string(vdom_or_component)` → `str`. It consults only `tagName`/`attributes`/
    `children`: **event handlers, `inlineJavaScript`, and `importSource` vanish silently**, and a
    web-module component serializes as a bare unknown tag. It **lower-cases every attribute name**
    except `data-*`/`aria-*` — `{"className": "card"}` becomes `classname="card"`, which is dead
    HTML. If the string is the destination, write `"class"` and `"for"`. `style` is flattened with
    kebab-cased keys and **no unit inference** (`{"fontSize": 30}` yields invalid CSS even though
    the live renderer applies `30px`) — always put units in the string. Booleans follow lxml, not
    HTML: `{"checked": False}` can still emit `checked`; **omit the key** rather than set it false.
    A callable left in `attributes` raises `TypeError: Cannot convert callable attribute k=v to HTML`.
  - `string_to_reactpy(html, *transforms, strict=True, intercept_links=True)` → `VdomDict`. It
    **renames on the way in** (`class`→`className`, `for`→`htmlFor`, `checked`→`defaultChecked`,
    `accept-charset`→`acceptCharset`, `http-equiv`→`httpEquiv`, a `style` string → camelCase dict,
    `<input value>`→`defaultValue`, `<textarea>` text → `defaultValue`, `<option selected>` →
    `defaultValue` on the parent `<select>`, which also gains `multiple`). `intercept_links=True`
    puts a preventDefault-only `onClick` on **every** `<a>`, so links look dead — pass
    `intercept_links=False`. `infer_key_from_attributes` copies `key`→`id`→`name` into
    `attributes["key"]` for input/select/textarea, so two elements with the same `id` collide with
    `ValueError: Duplicate keys [...]`. Whitespace text nodes survive (`'\n  '` children).
    lxml picks the wrapper for you (`<p>a</p><p>b</p>` → a `div`; `<body>hi</body>` → a `span`) —
    never index children by position.
  - **It does not sanitize.** `<img src=x onerror="alert(1)">` comes back with
    `inlineJavaScript: {"onError": "alert(1)"}`, which the client `eval`s. Run a real sanitizer
    first. `*transforms` are one-arg callables applied to every node **after** the built-ins, and
    the return value replaces the node unconditionally — **a transform returning `None` deletes
    it**. Always return the model.
  - Errors: `TypeError: Expected html to be a string, not int`,
    `ValueError: Expected html string to contain HTML tags, but no tags were found.` (empty input
    returns `{"tagName": ""}` instead), and `HTMLParseError` — a subclass of
    `etree.LxmlSyntaxError`, **not** `ValueError`. `strict=False` sets `recover=True` and invents
    attribute names from malformed text; `strict` never catches unclosed tags or unknown entities.
    The parse is a full lxml document build per call — parse once at module level, or memoize.
    It also accepts `lxml`/`bs4`/`html5lib` transform objects (`AttributesToDict`,
    `ChildrenToList`, `ClassNameToClass`) — all or nothing. The ReactJS-era `to_html_string` /
    `html_to_vdom` names do not exist.
