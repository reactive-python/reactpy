## Overview

<p class="intro" markdown>

Your components will often need to display different things depending on different conditions. In ReactPy, you can conditionally render markup using Python syntax like `#!python if` statements and conditional expressions.

</p>

!!! summary "You will learn"

    -   How to return different markup depending on a condition
    -   How to conditionally include or exclude a piece of markup
    -   Conditional syntax shortcuts you'll encounter in ReactPy codebases

## Conditionally returning markup

Let's say you have a `#!python packing_list()` component rendering several `#!python item()`s, which can be marked as packed or not. Notice that some of the `#!python item()` calls have their `#!python is_packed` prop set to `#!python True` instead of `#!python False`. You want to add a checkmark (✔) to packed items if `#!python is_packed` is `#!python True`.

You can write this as an [`if`/`else` statement](https://docs.python.org/3/tutorial/controlflow.html#if-statements) like so:

```python linenums="0"
if is_packed:
    return html.li({"className": "item"}, f"{name} ✔")
return html.li({"className": "item"}, name)
```

If the `#!python is_packed` prop is `#!python True`, this code **returns a different VDOM tree.** With this change, some of the items get a checkmark at the end:

=== "app.py"

    ```python
    {% include "../../examples/conditional_rendering/if_else/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/conditional_rendering/if_else/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Try editing what gets returned in either case, and see how the result changes!

Notice how you're creating branching logic with Python's `#!python if` and `#!python return` statements. In ReactPy, control flow (like conditions) is handled by Python.

### Conditionally returning nothing with `None`

In some situations, you won't want to render anything at all. For example, say you don't want to show packed items at all. A component must return something — in ReactPy, that something is `#!python None`:

```python linenums="0"
if is_packed:
    return None
return html.li({"className": "item"}, name)
```

If `#!python is_packed` is true, the component will return nothing, `#!python None`. Otherwise, it will return markup to render.

=== "app.py"

    ```python
    {% include "../../examples/conditional_rendering/return_none/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/conditional_rendering/return_none/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

In practice, returning `#!python None` from a component isn't common because it might surprise a developer trying to render it. More often, you would conditionally include or exclude the component in the parent component. Here's how to do that!

## Conditionally including markup

In the previous example, you controlled which (if any!) VDOM tree would be returned by the component. You may already have noticed some duplication in the render output:

```python linenums="0"
html.li({"className": "item"}, f"{name} ✔")
```

is very similar to

```python linenums="0"
html.li({"className": "item"}, name)
```

Both of the conditional branches return `#!python html.li({"className": "item"}, ...)`:

```python linenums="0"
if is_packed:
    return html.li({"className": "item"}, f"{name} ✔")
return html.li({"className": "item"}, name)
```

While this duplication isn't harmful, it could make your code harder to maintain. What if you want to change the `#!python className`? You'd have to do it in two places in your code! In such a situation, you could conditionally include a little markup to make your code more [DRY.](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)

### Conditional (ternary) expression

Python has a compact syntax for writing a conditional expression — the [conditional expression](https://docs.python.org/3/reference/expressions.html#conditional-expressions) or "ternary operator".

Instead of this:

```python linenums="0"
if is_packed:
    return html.li({"className": "item"}, f"{name} ✔")
return html.li({"className": "item"}, name)
```

You can write this:

```python linenums="0"
return html.li({"className": "item"}, f"{name} ✔" if is_packed else name)
```

You can read it as _"if `#!python is_packed` is true, then render `#!python f"{name} ✔"`, otherwise render `#!python name`"_.

Now let's say you want to wrap the completed item's text into another HTML tag, like `#!html <del>` to strike it out. You can add even more newlines and parentheses so that it's easier to nest more markup in each of the cases:

=== "app.py"

    ```python
    {% include "../../examples/conditional_rendering/ternary/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/conditional_rendering/ternary/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This style works well for simple conditions, but use it in moderation. If your components get messy with too much nested conditional markup, consider extracting child components to clean things up. In ReactPy, markup is a part of your code, so you can use tools like variables and functions to tidy up complex expressions.

!!! info "Are these two examples fully equivalent?"

    If you're coming from an object-oriented programming background, you might assume that the two examples above are subtly different because one of them may create two different "instances" of `#!python html.li`. But VDOM dictionaries aren't "instances" because they don't hold any internal state and aren't real DOM nodes. They're lightweight descriptions, like blueprints. So these two examples, in fact, _are_ completely equivalent. [Preserving and Resetting State](./preserving-and-resetting-state.md) goes into detail about how this works.

### Excluding a child with a conditional

In JavaScript React you'll often see the logical AND operator used to render a child only when a condition holds:

```js linenums="0"
<li className="item">{name} {isPacked && "✔"}</li>
```

**There is no equivalent of this idiom in ReactPy.** Python's `#!python and` returns one of its operands rather than a renderable-agnostic `#!python False`, and ReactPy renders `#!python False` as the literal text `#!python "False"` instead of skipping it:

```python linenums="0"
# WRONG: renders "Photo of Tam False" when is_packed is False
return html.li({"className": "item"}, name, is_packed and "✔")
```

Reach for a conditional expression that yields an empty list, and unpack it:

```python linenums="0"
return html.li(
    {"className": "item"},
    name,
    *(["✔"] if is_packed else []),
)
```

Or build the children list up front, which reads better as the number of optional children grows:

```python linenums="0"
@component
def item(name, is_packed):
    content = [name]
    if is_packed:
        content.append("✔")
    return html.li({"className": "item"}, *content)
```

!!! warning "Don't put a number on the left side of a conditional expression"

    The classic `#!js messageCount && <p>New messages</p>` bug has an exact Python twin. `#!python and` returns the left operand when it is falsy, and ReactPy renders numbers as text — so `#!python count and html.p("New messages")` renders `#!python 0` rather than nothing when `#!python count` is `#!python 0`. Make the left side a genuine boolean test:

    ```python linenums="0"
    html.p("New messages") if count > 0 else None
    ```

### Conditionally assigning markup to a variable

When the shortcuts get in the way of writing plain code, try using an `#!python if` statement and a variable. Start by providing the default content you want to display, the name:

```python linenums="0"
item_content = name
```

Use an `#!python if` statement to reassign a VDOM expression to `#!python item_content` if `#!python is_packed` is `#!python True`:

```python linenums="0"
if is_packed:
    item_content = html.del_(f"{name} ✔")
```

Embed the variable in the returned VDOM tree, nesting the previously calculated expression inside the parent element:

```python linenums="0"
html.li({"className": "item"}, item_content)
```

This style is the most verbose, but it's also the most flexible:

=== "app.py"

    ```python
    {% include "../../examples/conditional_rendering/variable/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/conditional_rendering/variable/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Like before, this works not only for text, but for arbitrary markup too.

!!! info "Tags that collide with Python keywords"

    `#!python del` is a Python keyword, so the `#!html <del>` tag is spelled with a trailing underscore: `#!python html.del_`. The underscore is stripped before the tag name is emitted, so it still renders `#!html <del>`. The same rule covers `#!python html.import_`, `#!python html.object`, and friends — and dashes become underscores, so `#!html <data-table>` is `#!python html.data_table`.

If you're not familiar with Python, this variety of styles might seem overwhelming at first. However, learning them will help you read and write any Python code — and not just ReactPy components! Pick the one you prefer for a start, and then consult this reference again if you forget how the other ones work.

## Recap

-   To conditionally return different markup from a component, use `#!python if` statements and `#!python return`.
-   To render nothing, return `#!python None` from the component.
-   To tidy up duplicated markup, use a conditional expression: `#!python x if condition else y`.
-   Don't use `#!python and` to include a child — ReactPy renders `#!python False` as the text `#!python "False"`. Unpack an empty list instead.
-   For anything more complex, assign children to variables with `#!python if` statements.
