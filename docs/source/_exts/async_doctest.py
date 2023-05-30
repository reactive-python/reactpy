from doctest import DocTest, DocTestRunner
from textwrap import indent
from typing import Any

from sphinx.application import Sphinx
from sphinx.ext.doctest import DocTestBuilder
from sphinx.ext.doctest import setup as doctest_setup

test_template = """
import asyncio as __test_template_asyncio

async def __test_template__main():

    {test}

    globals().update(locals())

__test_template_asyncio.run(__test_template__main())
"""


class TestRunnerWrapper:
    def __init__(self, runner: DocTestRunner):
        self._runner = runner

    def __getattr__(self, name: str) -> Any:
        return getattr(self._runner, name)

    def run(self, test: DocTest, *args: Any, **kwargs: Any) -> Any:
        for ex in test.examples:
            ex.source = test_template.format(test=indent(ex.source, "    ").strip())
        return self._runner.run(test, *args, **kwargs)


class AsyncDoctestBuilder(DocTestBuilder):
    @property
    def test_runner(self) -> DocTestRunner:
        return self._test_runner

    @test_runner.setter
    def test_runner(self, value: DocTestRunner) -> None:
        self._test_runner = TestRunnerWrapper(value)


def setup(app: Sphinx) -> None:
    doctest_setup(app)
    app.add_builder(AsyncDoctestBuilder, override=True)
