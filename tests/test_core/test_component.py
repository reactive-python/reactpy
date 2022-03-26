import idom
from idom.testing import DisplayFixture


def test_component_repr():
    @idom.component
    def MyComponent(a, *b, **c):
        pass

    mc1 = MyComponent(1, 2, 3, x=4, y=5)

    expected = f"MyComponent({id(mc1):02x}, a=1, b=(2, 3), c={{'x': 4, 'y': 5}})"
    assert repr(mc1) == expected

    # not enough args supplied to function
    assert repr(MyComponent()) == "MyComponent(...)"


async def test_simple_component():
    @idom.component
    def SimpleDiv():
        return idom.html.div()

    assert SimpleDiv().render() == {"tagName": "div"}


async def test_simple_parameterized_component():
    @idom.component
    def SimpleParamComponent(tag):
        return idom.vdom(tag)

    assert SimpleParamComponent("div").render() == {"tagName": "div"}


async def test_component_with_var_args():
    @idom.component
    def ComponentWithVarArgsAndKwargs(*args, **kwargs):
        return idom.html.div(kwargs, args)

    assert ComponentWithVarArgsAndKwargs("hello", "world", myAttr=1).render() == {
        "tagName": "div",
        "attributes": {"myAttr": 1},
        "children": ["hello", "world"],
    }


async def test_display_simple_hello_world(display: DisplayFixture):
    @idom.component
    def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    await display.show(Hello)

    assert display.page.wait_for_selector("#hello")


async def test_pre_tags_are_rendered_correctly(display: DisplayFixture):
    @idom.component
    def PreFormated():
        return idom.html.pre(
            {"id": "pre-form-test"},
            idom.html.span("this", idom.html.span("is"), "some"),
            "pre-formated",
            " text",
        )

    await display.show(PreFormated)

    pre = await display.page.wait_for_selector("#pre-form-test")

    assert (
        await pre.evaluate("node => node.innerHTML")
    ) == "<span>this<span>is</span>some</span>pre-formated text"
