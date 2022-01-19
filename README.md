# IDOM &middot; [![Tests](https://github.com/idom-team/idom/workflows/Test/badge.svg?event=push)](https://github.com/idom-team/idom/actions?query=workflow%3ATest) [![PyPI Version](https://img.shields.io/pypi/v/idom.svg)](https://pypi.python.org/pypi/idom) [![License](https://img.shields.io/badge/License-MIT-purple.svg)](https://github.com/idom-team/idom/blob/main/LICENSE)


**Last updated:** 2022-01-19\
_Document generation aided by **Documatic**_

<ENTER SHORT PROJECT DESCRIPTION>
IDOM is a Python web framework for building **interactive websites without needing a
single line of Javascript**. These sites are built from small elements of functionality
like buttons text and images. IDOM allows you to combine these elements into reusable
"components" that can be composed together to create complex views.

Ecosystem independence is also a core feature of IDOM. It can be added to existing
applications built on a variety of sync and async web servers, as well as integrated
with other frameworks like Django, Jupyter, and Plotly Dash. Not only does this mean
you're free to choose what technology stack to run on, but on top of that, you can run
the exact same components wherever you need them. For example, you can take a component
originally developed in a Jupyter Notebook and embed it in your production application
without changing anything about the component itself.
<!---Documatic-section-group: arch-start--->


<!---Documatic-section-group: arch-end--->

<!---Documatic-section-group: helloworld-start--->


## Code Overview

The codebase has a 2-deep folder structure, with 31 in total.
<!---Documatic-section-helloworld: setup-start--->
The codebase is compatible with Python 3.10 and above, because of pipe type hint in `src/idom/testing.py`.
Install requirements with `pip install -r requirements.txt`.

Run `pip install -e .` in top-level directory to install
package in local directory.
Install from pypi with `pip install idom`.



<!---Documatic-section-helloworld: setup-end--->

<!---Documatic-section-helloworld: entrypoints-start--->


## Entrypoints

There are 0 source code entrypoints in top-level `__main__`/`__init__` files.


<!---Documatic-section-helloworld: entrypoints-end--->

<!---Documatic-section-helloworld: classes-start--->
The project has classes which are used in multiple functions:

* `idom.core.layout._ModelState` is a base class. 
* `idom.core.proto.ComponentType` is a base class. 
* `idom.core.proto.ComponentConstructor` is a base class. 
* `idom.sanic.Blueprint` is a base class. 

### client.idom.core.layout._ModelState

```python
class _ModelState (
        self,
        parent: Optional[_ModelState],
        index: int,
        key: Any,
        model: Ref[VdomJson],
        patch_path: str,
        children_by_key: Dict[str, _ModelState],
        targets_by_event: Dict[str, str],
        life_cycle_state: Optional[_LifeCycleState] = None,
    )
```

### client.idiom.proto.ComponentType

```python
class ComponentType
    
```

<!---Documatic-section-helloworld: classes-end--->

<!---Documatic-section-group: concept-start--->
## Concepts

To get a rough idea of how to write apps in IDOM, take a look at the tiny "hello
world" application below:

```python
from idom import component, html, run

@component
def App():
    return html.h1("Hello, World!")

run(App)
```
HTML with idiom example

```python
from idom import html

html.div(
    html.h1("My Todo List"),
    html.ul(
        html.li("Design a cool new app"),
        html.li("Build it"),
        html.li("Share it with the world!"),
    )
)
```
Your first components

```python
from idom import component, html, run


@component
def Photo():
    return html.img(
        {
            "src": "https://picsum.photos/id/237/500/300",
            "style": {"width": "50%"},
            "alt": "Puppy",
        }
    )


run(Photo)

```

Rendering data
```python
from idom import component, html, run


@component
def DataList(items, filter_by_priority=None, sort_by_priority=False):
    if filter_by_priority is not None:
        items = [i for i in items if i["priority"] <= filter_by_priority]
    if sort_by_priority:
        items = list(sorted(items, key=lambda i: i["priority"]))
    list_item_elements = [html.li(i["text"], key=i["id"]) for i in items]
    return html.ul(list_item_elements)


@component
def TodoList():
    tasks = [
        {"id": 0, "text": "Make breakfast", "priority": 0},
        {"id": 1, "text": "Feed the dog", "priority": 0},
        {"id": 2, "text": "Do laundry", "priority": 2},
        {"id": 3, "text": "Go on a run", "priority": 1},
        {"id": 4, "text": "Clean the house", "priority": 2},
        {"id": 5, "text": "Go to the grocery store", "priority": 2},
        {"id": 6, "text": "Do some coding", "priority": 1},
        {"id": 7, "text": "Read a book", "priority": 1},
    ]
    return html.section(
        html.h1("My Todo List"),
        DataList(tasks, filter_by_priority=1, sort_by_priority=True),
    )


run(TodoList)
```
<!---Documatic-section-group: concept-end--->

<!---Documatic-section-group: helloworld-end--->

<!---Documatic-section-group: dev-start--->


## Developers
<!---Documatic-section-dev: setup-start--->
* This project uses `pre-commit` to enforce code style on commit. Run `pre-commit install` in a terminal to setup
* Tests are present in `tests/` (using pytest)




<!---Documatic-section-dev: setup-end--->

<!---Documatic-section-dev: ci-start--->
The project uses GitHub Actions for CI/CD.

| CI File | Purpose |
|:----|:----|
| test | Executes on push for branch main, pull_request for branch main |
| publish-py |Executes on publish relase branch .This workflows will upload a Javscript Package using NPM to npmjs.org when a release is created |
| deploy-docs | Executes on push for branch main. his workflows will upload a Python Package using Twine when a release is created |
| codeql-analysis | Executes on push for branch main, pull_request for branch main |
| publish-js | Executes on publish relase branch  .This workflows will upload a Javscript Package using NPM to npmjs.org when a release is created |


# Resources

Follow the links below to find out more about this project

- [Try it Now](https://mybinder.org/v2/gh/idom-team/idom-jupyter/main?urlpath=lab/tree/notebooks/introduction.ipynb) - check out IDOM in a Jupyter Notebook.
- [Documentation](https://idom-docs.herokuapp.com/) - learn how to install, run, and use IDOM.
- [Community Forum](https://github.com/idom-team/idom/discussions) - ask questions, share ideas, and show off projects.
- [Contributor Guide](https://idom-docs.herokuapp.com/docs/developing-idom/contributor-guide.html) - see how you can help develop this project.
- [Code of Conduct](https://github.com/idom-team/idom/blob/main/CODE_OF_CONDUCT.md) - standards for interacting with this community.


<!---Documatic-section-dev: ci-end--->

<!---Documatic-section-group: dev-end--->

