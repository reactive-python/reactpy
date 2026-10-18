## Overview

<p class="intro" markdown>

You will build a small tic-tac-toe game. This tutorial assumes no prior ReactPy knowledge, and the techniques it covers — components, props, state, and lifting state up — are the ones you will use in every app you write.

</p>

!!! abstract "Note"

    This tutorial is for people who prefer to **learn by doing**. If you would rather meet each concept one at a time, start with [Your First Component](./your-first-component.md) instead.

The tutorial is divided into four sections:

-   [Setup for the tutorial](#setup-for-the-tutorial) gives you **a starting point**.
-   [The basics](#the-basics-components-props-and-state) teaches you **the fundamentals**: components, props, and state.
-   [Completing the game](#completing-the-game) teaches you **the most common techniques**.
-   [Adding time travel](#adding-time-travel) shows **why immutability matters**.

### What are you building?

You will build an interactive tic-tac-toe game. Here is the finished result:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/time_travel/app.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

If the code does not make sense yet, do not worry — that is the point of the tutorial. Play the game before you read it. You will notice a list to the right of the board that records every move and lets you jump back to any of them. That list is what the last section builds toward.

!!! abstract "Note"

    Throughout this tutorial, `app.py` is the file you edit, and the `styles.css` tab shows the stylesheet it relies on. ReactPy serves your components, not files on your disk, so the stylesheet is loaded into the page in your ASGI entry module. [Setup for the tutorial](#setup-for-the-tutorial) shows how.

## Setup for the tutorial

The code below is your starting point: a single square, with no interactivity.

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/square_starter/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

It should render one empty-looking square containing an `X`.

!!! abstract "Note"

    You can follow along in your own editor instead. You will need:

    1. Python 3.11 or newer, with `pip install reactpy[asgi] uvicorn[standard]`
    2. A file `app.py` containing the example above
    3. A file `styles.css` containing the stylesheet above
    4. A file `main.py` that mounts `app.py` and injects the stylesheet:

        ```python linenums="0"
        {% include "../../examples/tutorial_tic_tac_toe/square_starter/main.py" %}
        ```

    5. `uvicorn main:my_app`, then open the URL it prints

    If the setup fights you, do not let it stop you — follow along online and try the local setup again later. See [Creating a Standalone React App](./creating-a-react-app.md) for the details.

## The basics: components, props, and state

### Inspecting the starter code

The example defines a _component_. In ReactPy, a component is a function that returns what part of the interface should look like. Read it line by line:

```python linenums="0"
{% include "../../examples/tutorial_tic_tac_toe/square_starter/app.py" start="# start" %}
```

The first two lines are boilerplate: `#!python @component` turns the function below it into a component, and `#!python html` gives you a function for every HTML tag.

The `#!python def square():` line defines a function called `square`. Unlike React, ReactPy component names are **snake_case and lowercase** — there is no capital-letter rule, because ReactPy tells a component from an HTML tag by whether you *call* it, not by how it is spelled.

The `#!python return` line gives back a button. `#!python html.button(...)` is a call to a function, not an element literal: children come after the attribute dictionary as positional arguments, so `#!python "X"` is the text inside the button. `#!python {"className": "square"}` is that attribute dictionary, and `className` is the DOM attribute name — attribute keys are forwarded to the browser verbatim, so they keep React's camelCase spelling.

### Building the board

The board needs nine squares, not one. Copying the button twice is tempting:

```python linenums="0"
@component
def square():
    return html.button({"className": "square"}, "X"), html.button({"className": "square"}, "X")
```

That does not fail the way React's "adjacent JSX elements" error does. The comma builds a two-item *tuple*; ReactPy does not know you meant two children, coerces it with `#!python str()`, and the page shows the VDOM dictionaries as literal text:

```text
({'children': ['X'], 'attributes': {'className': 'square'}, 'tagName': 'button'}, ...)
```

Verified through `Layout.render()`: the model's only child is that string. If the page ever shows you a Python repr, a missing call or a stray comma is the usual cause. A component returns exactly one thing. To return several children, wrap them in a fragment with `#!python html.fragment(...)`, which groups children without adding an element of its own:

```python linenums="0"
@component
def square():
    return html.fragment(
        html.button({"className": "square"}, "X"),
        html.button({"className": "square"}, "X"),
    )
```

Now copy-paste your way to nine squares and... they come out in a single line, not a grid. Group them into rows with `#!python div`s carrying the `className` the stylesheet already defines, and number the squares so you can tell them apart:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/nine_squares/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

You now have a tic-tac-toe board. But you have a naming problem: the component is called `square` and renders a whole board. Rename it to `board`.

At this point your code should look like this:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/board/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

!!! abstract "Note"

    That is a lot of typing. Copying code from this page is fine, but you will learn more by typing each snippet at least once yourself.

### Passing data through props

Nine hardcoded buttons means nine places to change when a square's content becomes dynamic. Instead, extract a `square` component and give it the value to display — a _prop_:

```python linenums="0"
@component
def square(value):
    return html.button({"className": "square"}, value)
```

There is no JSX, so props are simply Python parameters. Call the component and pass the argument:

```python linenums="0"
square("A")
```

Update `board` to call `square` nine times, passing a different letter each time so you can see the values arrive:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/passing_props/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Notice how `#!python board` and `#!python square` are both called the same way, with no ceremony, while `#!python html.div` and `#!python html.button` are calls into the `html` object. Components are just functions you wrote; tags are functions ReactPy provides.

Props are read-only. `#!python square` cannot assign to `#!python value` to change what its parent passed, and ReactPy has no mechanism to help it try. Data flows down; to change it, the component that owns it must change it.

### Making an interactive component

Now make a square fill itself when clicked. Add a handler inside `square` and register it under `onClick`:

```python linenums="0"
@component
def square():
    async def handle_click(event):
        print("clicked!")

    return html.button({"className": "square", "onClick": handle_click})
```

A handler is a coroutine, and ReactPy calls it with exactly one argument — the event. Name it `event`, even if you ignore it.

Unlike React, there is no browser console to open: ReactPy components run on the server, so `#!python print` lands in the terminal running your app, next to the URL. Click a square several times and you will see the line repeat there.

!!! warning "Pitfall"

    The key must be camelCase `#!python onClick`. The React-looking `#!python on_click` is accepted and shipped to the browser like any other `#!python on*` key — and then nothing listens for it, because no browser event is named `on_click`. Verified: the server-side model holds a registered `on_click` handler while clicking the button leaves the component's state at `0`. The button renders, looks normal, and never fires, with no error and no log line anywhere. If a control does nothing, check the spelling of the key first. See [Responding to Events](./responding-to-events.md).

Next, make the square *remember* that it was clicked. ReactPy gives components memory with the `#!python use_state` hook, which returns the current value and the function that changes it:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/square_state/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python value, set_value = use_state(EMPTY_SQUARE)` unpacks a pair: the state you read and the setter you call. Its argument is the starting value, used only on the component's first render. Calling `#!python set_value` asks ReactPy to render the component again, and that render sees the new `value`.

The value is `#!python None`, meaning "empty", and ReactPy renders `#!python None` as nothing, so a fresh board is blank. It lives in a module-level constant annotated `#!python str | None`, which is what lets a type checker accept both `#!python None` and `"X"` in that square — without it, the type is inferred from `#!python None` alone and assigning a mark is flagged. See [Use State](../reference/use-state.md).

Note that ReactPy renders `#!python True` and `#!python False` as the *words* `True` and `False`, so `#!python None` is the only value that disappears — React's habit of writing `cond && <X/>` has no working Python equivalent. See [Conditional Rendering](./conditional-rendering.md).

Click each square and watch them fill independently. Nine `#!python square()` calls contain nine separate `#!python use_state` calls, and each one keeps its own value.

That is a defect, not a feature. Each square's value lives inside that square, so no other part of the program can see the whole board — which means nothing can answer "has someone won?". The next section fixes this by moving the state to where the whole board is visible.

## Completing the game

Right now the game has a serious limitation: nobody can win.

### Lifting state up

To detect a winner you need the whole board in one place. The fix is to move the state out of `square` and into `board`, which already renders all nine squares — a move called _lifting state up_.

`board` owns a list of nine values and passes each one down:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/lifting_state/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`square` is now stateless: it takes `value` to display and `on_click` to call, and remembers nothing. That is the shape of most components you will write — they take data in and report events out, and the state lives above them.

Note the spelling distinction, because both forms are correct in different places. `#!python on_click` above is a *Python parameter* — a prop name you invented, so it is snake_case like every other identifier you define. `#!python onClick` is the *attribute dictionary key* the browser needs, so it keeps its camelCase spelling. Naming a prop `#!python onClick` or writing the attribute key `#!python on_click` are both mistakes, in opposite directions.

Two details are worth pausing on.

First, the handler needs to know *which* square was clicked, but ReactPy hands a handler exactly one argument: the event. The answer is a factory, as `#!python handle_click(i)` does here — it returns the handler that closes over `#!python i`:

```python linenums="0"
def handle_click(i):
    async def inner(event):
        ...

    return inner


html.button({"onClick": handle_click(i)}, squares[i])
```

A `#!python lambda` is not available for this. It cannot be a coroutine, so ReactPy refuses it as a handler; `#!python functools.partial(handle_click, i)` over a two-parameter handler is the other shape which works — but prefer the factory. ReactPy unwraps a `#!python partial` before reading your code, yet it then looks for `#!python preventDefault()` and friends on your function's **first** parameter, and a `#!python partial` has already filled that one in. So a `#!python preventDefault()` inside a `#!python partial`-bound handler goes undetected and has to be declared with `#!python @event(prevent_default=True)`. The factory has no such problem: its inner `#!python async def inner(event)` still leads with the event, so detection finds what you wrote.

The factory has a sharp edge inside a loop — the closure captures the variable, not the value — which [Picking a key](#picking-a-key) demonstrates.

Second, `board` renders three rows by hand, so `square(...)` appears nine times with nine different indices. A loop is shorter, and once you write one you will need keys — see [Rendering Lists](./rendering-lists.md).

### Why immutability is important

Look closely at what the handler does before it calls the setter:

```python linenums="0"
next_squares = squares.copy()
next_squares[i] = "X"
set_squares(next_squares)
```

It copies the list, changes the copy, and hands the copy to the setter. There are two ways to change data: _mutate_ it in place, or replace it with a modified copy. The obvious Python code takes the first route, and it fails in a way that is hard to diagnose:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/mutating/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Click a square. Nothing happens — no error, no log line, no warning. The handler *runs*; the board just never changes.

Verified against this example: after three clicks on that square, the board is still nine empty cells. The cause is that `#!python set_squares(squares)` passes back the very same object that is already in state. ReactPy compares the new value against the current one, finds them equal, and skips the render — an optimisation that turns an in-place mutation into a silent no-op.

!!! warning "Pitfall"

    Mutate-then-set-the-same-object is the most common ReactPy bug and the quietest one. `#!python squares[i] = "X"` followed by `#!python set_squares(squares)` schedules no render at all. Neither does mutating without calling the setter. Always build a new list — `#!python squares.copy()`, a list comprehension, or slicing — and pass that. See [Updating Arrays in State](./updating-arrays-in-state.md).

Immutability earns its keep twice here. It is what makes the board update at all, and it is what lets the last section keep every past move around: because old lists are never modified, they stay valid and can be re-displayed later.

!!! info "Deep Dive"

    React's version of this section argues that immutability lets React skip re-rendering parts of the tree that did not change. That argument does not apply to ReactPy: there is no `#!python memo` and no render bailout, so a child component's body re-runs whenever its parent renders, even with identical props. Immutable data is still required — for the reason above, and so equality checks mean what you expect — but do not expect it to save you renders. See [You Might Not Need an Effect](./you-might-not-need-an-effect.md#caching-expensive-calculations).

### Taking turns

Players can fill squares, but only with `X`. Add a second piece of state to `board` for whose turn it is, and flip it after every move:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/taking_turns/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Squares now alternate `X` and `O`, and the status line above the board tracks the next player.

One defect remains: click a filled square and the other player overwrites it. That happens because the handler never checks whether the square is already taken. Return early instead of playing over it:

```python linenums="0"
async def inner(event):
    if squares[i]:
        return
    next_squares = squares.copy()
    ...
```

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/guarded_turns/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: clicking square 0 twice leaves `X` in place rather than replacing it with `O`, and the other squares still play.

The guard is the first line of the handler, before any state is built or set. Putting it after `#!python set_squares` would let the invalid move through and try to undo it — an expensive, error-prone shape. Return early, then proceed.

### Declaring a winner

Add a helper that checks the eight winning lines. It knows nothing about ReactPy, so read it as plain Python:

```python linenums="0"
def calculate_winner(squares):
    lines = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ]
    for a, b, c in lines:
        if squares[a] and squares[a] == squares[b] and squares[a] == squares[c]:
            return squares[a]
    return None
```

It returns `"X"`, `"O"`, or `#!python None`. Where you put it in the file does not matter; keeping it at the bottom means you do not scroll past it every time.

Call it in two places — to stop play after a win, and to write the status line:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/declaring_winner/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Get three in a row and the status changes to `Winner: X`, after which no square responds — the guard returns early because `#!python calculate_winner(squares)` is truthy.

Notice that the winner is not stored in state. It is computed from `#!python squares` during every render, which is both simpler and impossible to get out of sync. If a value can be derived from state you are already storing, do not add a second piece of state for it: two sources of truth drift, and one number cannot. See [Reacting to Input with State](./reacting-to-input-with-state.md).

The game is playable. What it cannot do is show you how it got here — which is where immutability finally pays off.

## Adding time travel

Because every move produced a *new* list instead of modifying the old one, the previous boards still exist. All that is left is to keep them.

The history is a list of boards, one per move:

```python linenums="0"
[
    # before the first move
    [None] * 9,
    # after the first move
    [None, None, None, None, "X", None, None, None, None],
    # after the second move
    [None, None, None, None, "X", None, None, None, "O"],
]
```

### Lifting state up, again

Add a `game` component above `board` to hold that history. It will also decide which move you are looking at, so `board` must stop owning state and start receiving what to draw.

Start by having `game` render `board` inside the layout the stylesheet expects, and keep the history and the current move as its own state. `board` keeps its own `handle_click`, but now reports the finished move upward through an `on_play` prop instead of storing it:

```python linenums="0"
@component
def game():
    history, set_history = use_state([[None] * 9])

    def handle_play(next_squares):
        set_history([*history, next_squares])

    current_move = len(history) - 1
    x_is_next = current_move % 2 == 0
    current_squares = history[current_move]

    return html.div(
        {"className": "game"},
        html.div(
            {"className": "game-board"},
            board(x_is_next, current_squares, handle_play),
        ),
        html.div({"className": "game-info"}, html.ol()),
    )
```

`#!python x_is_next` and `#!python current_squares` are not state. They are computed from `#!python history` during the render, which is why they cannot drift out of sync with it.

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/storing_history/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The game plays exactly as it did before — only now the whole history lives in one component that can see all of it.

### Showing the past moves

You have a list of moves in state; render it as a list of buttons. Where React reaches for `#!javascript map`, Python reaches for a comprehension or a loop:

```python linenums="0"
moves = []
for move in range(len(history)):
    description = f"Go to move #{move}" if move > 0 else "Go to game start"
    moves.append(html.li(html.button({"onClick": jump_to(move)}, description)))
```

Then render `#!python html.ol(moves)` inside the `game-info` div. Add a `#!python current_move` state variable and an empty `#!python jump_to(move)` that does nothing yet, so the list has somewhere to go:

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/showing_moves/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Make a few moves and the list grows: `Go to game start`, `Go to move #1`, `Go to move #2`. Clicking one does nothing, because `#!python jump_to` is still the placeholder — that is the next step.

!!! warning "Pitfall"

    With `REACTPY_DEBUG` on, the server logs `Key not specified for child in list ...` for every row. ReactPy is telling you the same thing React does: a list you will re-render needs a key on each item. It is a warning, not an error, so a list can ship without one — and misbehave later in ways that are hard to trace back. The fix is [Picking a key](#picking-a-key).

    A related trap: pass a **list**, not a generator. `#!python html.ol(html.li(...) for ... in ...)` skips the key check entirely, with the warning `Did not verify key-path integrity of children in generator ... - pass a sequence`, and an iterator stored in state is worse still — it is single-use, so the first render shows the rows and every later render shows nothing.

### Picking a key

When you re-render a list, ReactPy has to work out which item is which. It cannot read your intent, so you tell it: give each item a `key`.

```python linenums="0"
html.li({"key": move}, html.button({"onClick": jump_to(move)}, description))
```

`#!python key` is a reserved name, and it is spelled two different ways depending on what you are creating — mixing them up is a hard error:

| You are creating | Spell it | Passing it the other way raises |
| --- | --- | --- |
| an **element** | inside the attribute dict: `html.li({"key": move}, ...)` | `TypeError: Vdom.__call__() got an unexpected keyword argument 'key'` |
| a **component** | as a keyword: `row(item, key=item["id"])` | silently meaningless, since the dict is the attribute dict |

A key identifies an item across renders. Change a component's key and ReactPy destroys it and builds a fresh one, discarding its state — which is a useful trick on its own, and the subject of [Preserving and Resetting State](./preserving-and-resetting-state.md). Keys need only be unique among siblings, not globally.

For the move list, the move's index is a legitimate key: moves are never reordered, inserted in the middle, or deleted, so index and identity agree. That is the exception. When items can be added or removed, the array index stops identifying anything, and state quietly lands on the wrong row — use a real identifier instead. See [Rendering Lists](./rendering-lists.md).

### Implementing time travel

`#!python jump_to(move)` only has to say which move you are looking at:

```python linenums="0"
def jump_to(move):
    async def inner(event):
        set_current_move(move)

    return inner
```

And the values derived during render must follow `#!python current_move` rather than the end of the list:

```python linenums="0"
x_is_next = current_move % 2 == 0
current_squares = history[current_move]
```

Playing a move now has one more rule. If you jump back and play from there, the moves after that point are no longer the future — they are discarded:

```python linenums="0"
def handle_play(next_squares):
    next_history = history[: current_move + 1]
    next_history.append(next_squares)
    set_history(next_history)
    set_current_move(len(next_history) - 1)
```

The slice `#!python history[: current_move + 1]` keeps everything up to and including the move you jumped back to, dropping the rest, and `#!python set_current_move` puts you at the new end.

=== "app.py"

    ```python
    {% include "../../examples/tutorial_tic_tac_toe/time_travel/app.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/tutorial_tic_tac_toe/game.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified against this file: play three moves to put `X` in the corners, click **Go to game start**, and the board is empty again with `Next player: X`. Jump to `Go to move #1`, play a different square, and the list retracts to two entries — the abandoned branch is gone.

None of that would work if the handlers mutated `#!python squares` in place. Every stored board would be the same list, and rewinding would show the current game. This is the payoff for the rule from [Why immutability is important](#why-immutability-is-important).

!!! warning "Pitfall"

    Do not store one board and a separate list of moves that points into it. The history must own the boards, and the boards must never change once stored. If you find yourself reaching for `#!python deepcopy` here, that is a sign something is still being mutated — with the code above, the boards are never modified after they are created, so a plain slice is enough.

### Final cleanup

The finished game holds its state in three places, each as low as it can be while still seeing what it needs:

-   `game` owns `#!python history` and `#!python current_move`, because it renders both the board and the move list.
-   `board` owns nothing. It receives `#!python x_is_next`, `#!python squares`, and `#!python on_play`.
-   `square` owns nothing. It receives `#!python value` and `#!python on_click`.

That is the pattern this tutorial was built around. State belongs to the component that needs it and to every component above it — no lower, because then a sibling cannot see it, and no higher, because then unrelated renders redo the work. When two components need the same data, lift it to their nearest common ancestor.

### Wrapping up

-   A component returns **exactly one thing** — an element, another component, a `#!python str`, or `#!python None`. Several children go inside `#!python html.fragment(...)` or a real element: `#!python return [a, b]` does not render two nodes, it renders the list's `#!python repr` as text.
-   Props are ordinary Python parameters, and they are read-only.
-   `#!python use_state` gives a component memory; calling the setter re-renders it.
-   Handlers take exactly one argument, the event. Extra context is bound on the Python side, usually with a factory function.
-   Never mutate a list you have put in state — copy it, or the setter silently does nothing.
-   Derive what you can during render instead of storing it: `#!python winner`, `#!python x_is_next`, `#!python current_squares`.
-   Lift state to the lowest component that can see everything that needs it.
-   Give list items a `#!python key` — in the attribute dict for elements, as a keyword for components.
-   Time travel is free once your data is immutable, and impossible when it is not.

## Related

-   [Quick Start](./quick-start.md) — the same building blocks at a faster pace
-   [Your First Component](./your-first-component.md) — components and props in more depth
-   [State: A Component's Memory](./state-a-components-memory.md) — how `#!python use_state` behaves
-   [Adding Interactivity](./responding-to-events.md) — events, handlers, and `@event` options
-   [Updating Arrays in State](./updating-arrays-in-state.md) — replace, never mutate
-   [Sharing State Between Components](./sharing-state-between-components.md) — lifting state up
-   [Rendering Lists](./rendering-lists.md) — keys, and when the index is the wrong choice
-   [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md) — the next step once a component has too many state variables
