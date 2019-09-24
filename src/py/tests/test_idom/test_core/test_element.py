import idom


async def test_simple_element():
    @idom.element
    async def simple_div(self):
        return idom.html.div()

    sd = simple_div()

    assert await sd.render() == {"tagName": "div"}
    # can render more than once without update
    assert await sd.render() == {"tagName": "div"}

    sd.update()
    assert await sd.render() == {"tagName": "div"}


async def test_simple_parameterized_element():
    @idom.element
    async def simple_param_element(self, tag):
        return idom.vdom(tag)

    spe = simple_param_element("div")
    assert await spe.render() == {"tagName": "div"}
    spe.update("img")
    assert await spe.render() == {"tagName": "img"}


async def test_simple_stateful_element():
    @idom.element(state="tag")
    async def simple_stateful_element(self, tag):
        return idom.vdom(tag)

    ssd = simple_stateful_element("div")
    assert await ssd.render() == {"tagName": "div"}
    ssd.update()
    assert await ssd.render() == {"tagName": "div"}
    ssd.update("img")
    assert await ssd.render() == {"tagName": "img"}
    ssd.update()
    assert await ssd.render() == {"tagName": "img"}
