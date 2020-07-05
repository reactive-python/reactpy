import pytest
import idom


def test_element_repr():
    @idom.element
    async def MyElement(a, *b, **c):
        pass

    m_e = MyElement(1, 2, 3, x=4, y=5)

    expected = f"test_element_repr.<locals>.MyElement({m_e.id}, a=1, b=(2, 3), c={{'x': 4, 'y': 5}})"
    assert repr(m_e) == expected


def test_element_function_is_coroutine():
    with pytest.raises(TypeError, match="Expected a coroutine function"):

        @idom.element
        def non_coroutine_func():
            pass


async def test_simple_element():
    @idom.element
    async def simple_div():
        return idom.html.div()

    sd = simple_div()

    assert await sd.render() == {"tagName": "div"}


async def test_simple_parameterized_element():
    @idom.element
    async def simple_param_element(tag):
        return idom.vdom(tag)

    spe = simple_param_element("div")
    assert await spe.render() == {"tagName": "div"}


async def test_element_with_var_args():
    @idom.element
    async def element_with_var_args_and_kwargs(*args, **kwargs):
        return idom.html.div(kwargs, args)

    element = element_with_var_args_and_kwargs("hello", "world", myAttr=1)

    assert (await element.render()) == {
        "tagName": "div",
        "attributes": {"myAttr": 1},
        "children": ["hello", "world"],
    }


def test_display_simple_hello_world(driver, display):
    @idom.element
    async def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element_by_id("hello")
