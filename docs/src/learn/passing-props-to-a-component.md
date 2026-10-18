## Overview

<p class="intro" markdown>

ReactPy components use _props_ to communicate with each other. Every parent component can pass some information to its child components by giving them props. Props might remind you of HTML attributes, but you can pass any Python value through them, including dictionaries, lists, and functions.

</p>

!!! summary "You will learn"

    -   How to pass props to a component
    -   How to read props from a component
    -   How to specify default values for props
    -   How to pass some markup to a component
    -   How props change over time

## Familiar props

Props are the information that you pass to a tag. For example, `#!python className`, `#!python src`, `#!python alt`, `#!python width`, and `#!python height` are some of the props you can pass to an `#!html <img>`:

=== "app.py"

    ```python
    {% include "../../examples/passing_props_to_a_component/familiar/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/passing_props_to_a_component/familiar/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The props you can pass to an `#!python html.img` tag are predefined (the browser conforms to [the HTML standard](https://html.spec.whatwg.org/multipage/embedded-content.html#the-img-element)), and they keep their familiar camelCase spelling because they are handed straight to the DOM. But you can pass any props to _your own_ components, such as `#!python avatar()`, to customize them. Here's how!

## Passing props to a component

In this code, the `#!python profile()` component isn't passing any props to its child component, `#!python avatar()`:

```python linenums="0"
@component
def profile():
    return avatar()
```

You can give `#!python avatar()` some props in two steps.

### Step 1: Pass props to the child component

First, pass some props to `#!python avatar()`. For example, let's pass two props: `#!python person` (a dictionary), and `#!python size` (a number):

```python linenums="0"
@component
def profile():
    return html.div(
        avatar(
            person={"name": "Lin Lanying", "image_id": "1bX5QH6"},
            size=100,
        ),
    )
```

Unlike an HTML tag, a component you write takes its props as ordinary Python arguments. There is no attributes dictionary here — the values land directly in the function's parameters.

### Step 2: Read props inside the child component

You read props by listing their names `#!python person, size` directly after `#!python def avatar`. This lets you use them inside the `#!python avatar()` code, like you would with a variable.

```python linenums="0"
@component
def avatar(person, size):
    # person and size are available here
    ...
```

Add some logic to `#!python avatar()` that uses the `#!python person` and `#!python size` props for rendering, and you're done.

Now you can configure `#!python avatar()` to render in many different ways with different props. Try tweaking the values!

=== "app.py"

    ```python
    {% include "../../examples/passing_props_to_a_component/passing/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/passing_props_to_a_component/passing/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Props let you think about parent and child components independently. For example, you can change the `#!python person` or the `#!python size` props inside `#!python profile()` without having to think about how `#!python avatar()` uses them. Similarly, you can change how `#!python avatar()` uses these props, without looking at `#!python profile()`.

You can think of props like "knobs" that you can adjust. They serve the same role as arguments serve for functions—in fact, props _are_ the only argument to your component! A component is nothing but a Python function, and a function can only accept arguments.

!!! warning "Every argument is a prop"

    In JavaScript, a component receives a single `props` object which you then _destructure_ into `#!js function Avatar({ person, size })`. Python needs no such ceremony: the parameters _are_ the props.

    ```python linenums="0"
    @component
    def avatar(person, size): ...
    ```

    is already the direct, Pythonic form of that idea. But it means every parameter you declare is a prop a caller can pass by name — so keep the signature of a component to the values it actually renders.

## Specifying a default value for a prop

If you want to give a prop a default value to fall back on when no value is specified, put `#!python =` and the default value right after the parameter:

```python linenums="0"
@component
def avatar(person, size=100):
    # ...
```

Now, if `#!python avatar(person=...)` is rendered with no `#!python size` prop, the `#!python size` will be set to `#!python 100`.

The default value is used only when the caller omits the argument entirely. If you pass `#!python size=None` or `#!python size=0`, the default value will **not** be used — Python applies defaults for missing arguments, not for "empty" ones.

=== "app.py"

    ```python
    {% include "../../examples/passing_props_to_a_component/defaults/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/passing_props_to_a_component/defaults/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

## Forwarding props with keyword argument unpacking

Sometimes, passing props gets very repetitive:

```python linenums="0"
@component
def profile(person, size, is_sepia, thick_border):
    return html.div(
        {"className": "card"},
        avatar(
            person=person,
            size=size,
            is_sepia=is_sepia,
            thick_border=thick_border,
        ),
    )
```

There's nothing wrong with repetitive code—it can be more legible. But at times you may value conciseness. Some components forward all of their props to their children, like this `#!python profile()` does with `#!python avatar()`. Because they don't use any of their props directly, it can make sense to use Python's keyword argument unpacking instead:

```python linenums="0"
@component
def profile(**props):
    return html.div({"className": "card"}, avatar(**props))
```

This forwards all of `#!python profile()`'s props to the `#!python avatar()` without listing each of their names. Inside the function, `#!python props` is a plain dictionary, so you can also merge or filter it before forwarding.

**Use unpacking with restraint.** If you're using it in every other component, something is wrong. It hides the component's real interface, so neither your editor nor a reader can tell which props it accepts. Often, it indicates that you should split your components and pass children as arguments. More on that next!

=== "app.py"

    ```python
    {% include "../../examples/passing_props_to_a_component/forwarding/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/passing_props_to_a_component/forwarding/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

## Passing children to a component

It is common to nest built-in browser tags:

```python linenums="0"
html.div(html.img())
```

Sometimes you'll want to nest your own components the same way:

```python linenums="0"
card(avatar())
```

Anything you pass positionally lands in a `#!python *args` parameter of the parent component, which is the ReactPy equivalent of React's `#!js children` prop. For example, the `#!python card()` component below collects its children and renders them inside a wrapper `#!html <div>`:

=== "app.py"

    ```python
    {% include "../../examples/passing_props_to_a_component/children/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/passing_props_to_a_component/children/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Try replacing the `#!python avatar()` inside `#!python card()` with some text to see how the `#!python card()` component can wrap any nested content. It doesn't need to "know" what's being rendered inside of it. You will see this flexible pattern in many places.

You can think of a component with a `#!python *children` parameter as having a "hole" that can be "filled in" by its parent components with arbitrary markup. You will often use children for visual wrappers: panels, grids, etc.

!!! info "Keyword-only children"

    Because positional arguments become children, a component that accepts both should make its props keyword-only to avoid an ambiguous signature:

    ```python linenums="0"
    @component
    def card(*children, title=None):
        return html.div({"className": "card"}, title, *children)
    ```

    Now `#!python title=` can never be mistaken for a child.

## How props change over time

The `#!python clock()` component below receives two props from its parent component: `#!python color` and `#!python time`.

Try changing the color in the select box below:

=== "app.py"

    ```python
    {% include "../../examples/passing_props_to_a_component/changing/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This example illustrates that **a component may receive different props over time.** Props are not always static! Here, the `#!python time` prop changes every second, and the `#!python color` prop changes when you select another color. Props reflect a component's data at any point in time, rather than only in the beginning.

However, props are [immutable](https://en.wikipedia.org/wiki/Immutable_object)—a term from computer science meaning "unchangeable". When a component needs to change its props (for example, in response to a user interaction or new data), it will have to "ask" its parent component to pass it _different props_—a new set of arguments! ReactPy re-renders the child with those new values rather than editing the old ones in place.

!!! warning "Don't try to change props"

    When you need to respond to user input (like changing the selected color), you will need to "set state", which you can learn about in [State: A Component's Memory](./state-a-components-memory.md). Assigning to a prop parameter inside a component only rebinds the local name; the parent's value is untouched, and the next render overwrites it anyway.

## Recap

-   To pass props, add them as arguments to the component call, just like you would with an HTML tag's attributes.
-   To read props, list them as parameters: `#!python def avatar(person, size)`.
-   You can specify a default value like `#!python size=100`, which is used when the caller omits the argument.
-   You can forward all props with `#!python def profile(**props)` and `#!python avatar(**props)`, but don't overuse it!
-   Nested children like `#!python card(avatar())` arrive as a `#!python *children` parameter.
-   Props are read-only snapshots in time: every render receives a new version of props.
-   You can't change props. When you need interactivity, you'll need to set state.
