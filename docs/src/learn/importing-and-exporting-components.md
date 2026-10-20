## Overview

<p class="intro" markdown>

The magic of components lies in their reusability: you can create components that are composed of other components. But as you nest more and more components, it often makes sense to start splitting them into different files. This lets you keep your files easy to scan and reuse components in more places.

</p>

!!! summary "You will learn"

    -   What a root component module is
    -   How to import a component from another file
    -   How ReactPy expresses "private" and "public" components
    -   How to import and export multiple components from one file
    -   How to split components into multiple files

## The root component module

In [Your First Component](./your-first-component.md), you made a `#!python profile` component and a `#!python gallery` component that renders it:

=== "app.py"

    ```python
    {% include "../../examples/importing_and_exporting_components/one_file/app.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/importing_and_exporting_components/styles.css" %}
    ```

These currently live in a single module. Whichever module holds the component you hand to an executor is your **root component module** — the ASGI executor in [Creating a Standalone React App](./creating-a-react-app.md) takes that component directly:

```python linenums="0"
from reactpy.executors.asgi import ReactPy

from app import gallery

my_app = ReactPy(gallery)
```

Which module plays this role depends on your executor. The middleware executor takes dotted paths instead, e.g. `#!python ["my_components.hello_world"]`, and the CSR executor takes a path to a file whose `#!python root` component it mounts.

## Exporting and importing a component

What if you want to change the landing screen in the future and put a list of science books there? Or place all the profiles somewhere else? It makes sense to move `#!python gallery` and `#!python profile` into their own module. This makes them more modular and reusable in other files. You can move a component in three steps:

1.  **Make** a new Python file to put the components in.
2.  **Define** your component functions in that file. Unlike JavaScript, Python has no `export` keyword — every name defined at module level is importable.
3.  **Import** it in the module where you'll use the component.

Here both `#!python profile` and `#!python gallery` have moved into a new file called `#!python gallery.py`. Now `#!python app.py` imports `#!python gallery` from it:

=== "app.py"

    ```python
    {% include "../../examples/importing_and_exporting_components/private/app.py" %}
    ```

=== "gallery.py"

    ```python
    {% include "../../examples/importing_and_exporting_components/private/gallery.py" %}
    ```

Notice how this example is broken down into two component files now:

1.  `#!python gallery.py`:
    -   Defines the `#!python _profile` component, which is only used within the same file and is kept private.
    -   Makes `#!python gallery` the public component of the module.
2.  `#!python app.py`:
    -   Imports `#!python gallery` from `#!python gallery.py`.
    -   Defines the root `#!python app` component.

!!! abstract "Note"

    ReactPy does not care which module a component is defined in, so unlike ReactJS there is no distinction between "default" and "named" exports. `#!python from gallery import gallery, profile` and two separate import statements mean the same thing.

## Public and private components

ReactJS lets you keep a component unexported so that only its own file can use it. Python has no equivalent enforcement, but it has two widely respected conventions that express the same intent.

A leading underscore marks a name as private to its module:

```python linenums="0"
@component
def _profile():
    ...
```

And `#!python __all__` lists the names a module publishes. It is what a star import exports, and what linters and type checkers read to decide what is public API:

```python linenums="0"
__all__ = ["gallery"]
```

This is why `#!python _profile` is both underscore-prefixed and absent from `#!python __all__` in the example above.

!!! warning "Pitfall"

    These conventions are advisory, not enforced. `#!python from gallery import _profile` still works, because Python has no `private` keyword. Do not reach for underscore-prefixed names from another module, and do not rely on them being unavailable — treat a broken convention as a bug in the importing code, not as protection.

!!! info "Deep Dive"

    #### Naming modules and components

    Because imports name modules rather than files, give both meaningful names. `#!python scientists.py` defining `#!python gallery` and `#!python _profile` reads better than `#!python utils.py` defining `#!python Gallery`, and it also keeps you consistent with the rest of the docs, which write components in `#!python snake_case`.

    Components should still be *called* everywhere they are used, so a component used by two modules must be imported in both of them. There is no global component registry to fall back on.

## Exporting and importing multiple components from the same file

What if you want to show just one `#!python profile` instead of a gallery? Then `#!python app.py` needs `#!python profile` too. Add it to the module's `#!python __all__` and import it by name:

=== "app.py"

    ```python
    {% include "../../examples/importing_and_exporting_components/public/app.py" %}
    ```

=== "gallery.py"

    ```python
    {% include "../../examples/importing_and_exporting_components/public/gallery.py" %}
    ```

Now `#!python gallery.py` publishes both components:

-   `#!python gallery.py`:
    -   Lists `#!python gallery` and `#!python profile` in `#!python __all__`.
-   `#!python app.py`:
    -   Imports both `#!python gallery` and `#!python profile` from `#!python gallery.py`.
    -   Renders each of them.

## Recap

You've learned:

-   What a root component module is, and that it depends on your executor
-   How to import a component from another file
-   How ReactPy expresses public and private components with `#!python __all__` and a leading underscore
-   How to export multiple components from the same file

## Next Steps

Now that your components can live in separate files, continue to [Passing Props to a Component](./passing-props-to-a-component.md) to make them configurable.
