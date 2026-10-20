# <img src="https://raw.githubusercontent.com/reactive-python/reactpy/main/branding/svg/reactpy-logo-square.svg" align="left" height="45"/> ReactPy

<p>
    <a href="https://github.com/reactive-python/reactpy/actions/workflows/check.yml">
        <img src="https://github.com/reactive-python/reactpy/actions/workflows/check.yml/badge.svg">
    </a>
    <a href="https://pypi.org/project/reactpy/">
        <img src="https://img.shields.io/pypi/v/reactpy.svg?label=PyPI">
    </a>
    <a href="https://github.com/reactive-python/reactpy/blob/main/LICENSE.md">
        <img src="https://img.shields.io/badge/License-MIT-purple.svg">
    </a>
    <a href="https://reactpy.dev/">
        <img src="https://img.shields.io/website?down_message=offline&label=Docs&logo=read-the-docs&logoColor=white&up_message=online&url=https%3A%2F%2Freactpy.dev%2Fdocs%2Findex.html">
    </a>
    <a href="https://discord.gg/uNb5P4hA9X">
        <img src="https://img.shields.io/discord/1111078259854168116?label=Discord&logo=discord">
    </a>
</p>

[ReactPy](https://reactpy.dev/) is a library for building user interfaces in Python without Javascript. ReactPy interfaces are made from components that look, feel, and behave similar to those found in [ReactJS](https://reactjs.org/). By using the server-side executor, you can leverage Python's full capabilities for rendering and managing your UI, keeping the logic on the server while the client remains lightweight.

Designed with simplicity in mind, ReactPy can be used by those with minimal web development experience while also being powerful enough to grow with your ambitions. Additionally, autonomous LLM agents can leverage the [compacted documentation](AGENTS_EXTERNAL.md) to develop with ReactPy efficiently.

# At a Glance

To get a rough idea of how to write apps in ReactPy, take a look at this tiny _Hello World_ application.

```python
from reactpy import component, html
from reactpy.executors.asgi import ReactPy

@component
def hello_world():
    return html.h1("Hello, World!")

app = ReactPy(hello_world)
```

# Resources

Follow the links below to find out more about this project.

- [Documentation for Humans](https://reactpy.dev/)
- [Documentation for Agents (pre-compacted singleton)](AGENTS_EXTERNAL.md)
- [GitHub Discussions](https://github.com/reactive-python/reactpy/discussions)
- [Discord](https://discord.gg/uNb5P4hA9X)
- [Contributor Guide](https://reactpy.dev/docs/about/contributor-guide.html)
