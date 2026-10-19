## Overview

<p class="intro" markdown>

_Components_ are one of the core concepts of ReactPy. They are the foundation upon which you build user interfaces (UI), which makes them the perfect place to start your ReactPy journey!

</p>

!!! summary "You will learn"

    -   What a component is
    -   What role components play in a ReactPy application
    -   How to write your first ReactPy component

## Components: UI building blocks

On the Web, HTML lets us create rich structured documents with its built-in set of tags like `#!html <h1>` and `#!html <li>`:

```html linenums="0"
<article>
    <h1>My First Component</h1>
    <ol>
        <li>Components: UI Building Blocks</li>
        <li>Defining a Component</li>
        <li>Using a Component</li>
    </ol>
</article>
```

This markup represents this article `#!html <article>`, its heading `#!html <h1>`, and an (abbreviated) table of contents as an ordered list `#!html <ol>`. Markup like this, combined with CSS for style, and Python for interactivity, lies behind every sidebar, avatar, modal, dropdown—every piece of UI you see on the Web.

ReactPy lets you combine your markup, CSS, and Python into custom "components", **reusable UI elements for your app.** The table of contents code you saw above could be turned into a `#!python table_of_contents()` component you could render on every page. Under the hood, it still uses the same HTML tags like `#!python html.article`, `#!python html.h1`, etc.

Just like with HTML tags, you can compose, order and nest components to design whole pages. For example, the documentation page you're reading is made out of ReactPy components:

```python linenums="0"
html.div(
    html.header(
        search_bar(),
        html.a({"href": "/docs"}, "Docs"),
    ),
    sidebar(),
    html.main(
        table_of_contents(),
        documentation_text(),
    ),
)
```

As your project grows, you will notice that many of your designs can be composed by reusing components you already wrote, speeding up your development. Our table of contents above could be added to any screen with `#!python table_of_contents()`! You can even jumpstart your project with components shared by the community.

## Defining a component

Traditionally when creating web pages, web developers marked up their content and then added interaction by sprinkling on some JavaScript. This worked great when interaction was a nice-to-have on the web. Now it is expected for many sites and all apps. ReactPy puts interactivity first while still using the same technology: **a ReactPy component is a Python function that you can _sprinkle with markup_.** Here's what that looks like:

=== "app.py"

    ```python
    {% include "../../examples/your_first_component/profile.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    img {
        height: 200px;
    }
    ```

=== ":material-play: Run"

And here's how to build a component:

### Step 1: Import what you need

Every component needs the `#!python @component` decorator and the `#!python html` tag constructor:

```python linenums="0"
from reactpy import component, html
```

Unlike ReactJS, there is no `export` statement. To use a component from another file you import it like any other Python object, which you will learn about in [Importing and Exporting Components](./importing-and-exporting-components.md).

### Step 2: Define the function

With `#!python def profile():` you define a Python function with the name `#!python profile`. The `#!python @component` decorator turns that function into something ReactPy can render.

!!! warning "Pitfall"

    ReactPy components are ordinary Python functions, so follow Python's [naming conventions](https://peps.python.org/pep-0008/#function-and-variable-names) and write them in `#!python snake_case`.

    The ReactJS rule that "component names must start with a capital letter" **does not apply**. ReactJS needs that rule to tell components apart from HTML tags in its markup syntax. ReactPy has no markup syntax: HTML tags are reached through `#!python html.` and components are called directly, so the difference is already unambiguous.

### Step 3: Add markup

The component returns an `#!python html.img` element with `#!python src` and `#!python alt` attributes. There is no JSX or PSX in ReactPy — a tag is a normal Python call whose **first argument is a dictionary of attributes** and whose remaining arguments are its children.

Return statements can be written all on one line when the element is short:

```python linenums="0"
return html.h1("Amazing scientists")
```

For anything longer, wrap the element in parentheses rather than relying on a backslash continuation:

```python linenums="0"
return html.img(
    {"src": "https://i.imgur.com/MK3eW3As.jpg", "alt": "Katherine Johnson"}
)
```

## Using a component

Now that you've defined your `#!python profile` component, you can nest it inside other components. For example, you can define a `#!python gallery` component that uses multiple `#!python profile` components:

=== "app.py"

    ```python
    {% include "../../examples/your_first_component/gallery.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    img {
        margin: 0 10px 10px 0;
        height: 90px;
    }
    ```

=== ":material-play: Run"

### What the browser sees

Notice the difference in how the two kinds of calls are made:

-   `#!python html.section(...)` and `#!python html.h1(...)` are attributes on the `#!python html` object, so ReactPy knows they are HTML tags.
-   `#!python profile()` is a function you wrote and decorated with `#!python @component`, so ReactPy knows it is a component.

And `#!python profile` contains even more HTML: `#!python html.img`. In the end, this is what the browser sees:

```html linenums="0"
{% include "../../examples/your_first_component/browser_output.html" %}
```

### Nesting and organizing components

Components are regular Python functions, so you can keep multiple components in the same file. This is convenient when components are relatively small or tightly related to each other. If this file gets crowded, you can always move `#!python profile` to a separate file. You will learn how to do this shortly on the [page about imports.](./importing-and-exporting-components.md)

Because the `#!python profile` components are rendered inside `#!python gallery`—even several times!—we can say that `#!python gallery` is a **parent component,** rendering each `#!python profile` as a "child". This is part of the magic of ReactPy: you can define a component once, and then use it in as many places and as many times as you like.

!!! warning "Pitfall"

    Components can render other components, but **you must never nest their definitions:**

    ```python linenums="0"
    {% include "../../examples/your_first_component/nested_component_definition.py" %}
    ```

    Instead, define every component at the top level of your module:

    ```python linenums="0"
    {% include "../../examples/your_first_component/gallery.py" start="# start" %}
    ```

    Here is why. When ReactPy re-renders `#!python gallery`, it matches each child against the child from the previous render by the **identity of its function**. A component defined inside another function is a brand new function object every time the parent runs, so ReactPy concludes the old child is gone: it unmounts the previous `#!python profile`, throws away its state and Effects, and mounts a fresh one. Rendering still looks correct, which makes this bug easy to miss and hard to trace.

    When a child component needs some data from a parent, [pass it by props](./passing-props-to-a-component.md) instead of nesting definitions.

!!! info "Deep Dive"

    #### Components all the way down

    Your ReactPy application begins at a "root" component. This is the component you hand to an executor — for example the `#!python hello_world` component passed to `#!python ReactPy` in [Creating a Standalone React App](./creating-a-react-app.md).

    Most ReactPy apps use components all the way down. This means that you won't only use components for reusable pieces like buttons, but also for larger pieces like sidebars, lists, and ultimately, complete pages! Components are a handy way to organize UI code and markup, even if some of them are only used once.

    Because your components run on the server, ReactPy can also render them into the initial HTML response instead of waiting for a browser to do the work. See [Add React to an Existing Project](./add-react-to-an-existing-project.md) to render components inside pages you already have.

    Still, many websites only use ReactPy to [add interactivity to existing HTML pages.](./add-react-to-an-existing-project.md#using-react-for-a-part-of-your-existing-page) They have many root components instead of a single one for the entire page. You can use as much—or as little—ReactPy as you need.

## Recap

You've just gotten your first taste of ReactPy! Let's recap some key points.

-   ReactPy lets you create components, **reusable UI elements for your app.**
-   In a ReactPy app, every piece of UI is a component.
-   ReactPy components are regular Python functions except:

    1. They are decorated with `#!python @component`.
    2. They return elements built with `#!python html`.

-   Attributes are a `#!python dict`, children are the remaining arguments, and both are ordinary Python — which means `#!python for` loops, `#!python if` statements, and variables work exactly as you would expect.

## Next Steps

Check out [Importing and Exporting Components](./importing-and-exporting-components.md) to organize components across files, or jump straight to [Passing Props to a Component](./passing-props-to-a-component.md) to make yours configurable.
