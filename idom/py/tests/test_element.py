import pytest

import idom


async def test_simple_element():
    @idom.element
    def simple_div(self):
        return idom.nodes.div()

    sd = simple_div()

    assert await sd.render() == {"tagName": "div"}

    with pytest.raises(RuntimeError):
        # no update was applied after the last render
        assert await sd.render()

    sd.update()
    assert await sd.render() == {"tagName": "div"}


async def test_simple_parameterized_element():
    @idom.element
    def simple_param_element(self, tag):
        return idom.node(tag)

    spe = simple_param_element("div")
    assert await spe.render() == {"tagName": "div"}
    spe.update("img")
    assert await spe.render() == {"tagName": "img"}


async def test_simple_stateful_element():
    @idom.element(state="tag")
    def simple_stateful_element(self, tag):
        return idom.node(tag)

    ssd = simple_stateful_element("div")
    assert await ssd.render() == {"tagName": "div"}
    ssd.update()
    assert await ssd.render() == {"tagName": "div"}
    ssd.update("img")
    assert await ssd.render() == {"tagName": "img"}
    ssd.update()
    assert await ssd.render() == {"tagName": "img"}
