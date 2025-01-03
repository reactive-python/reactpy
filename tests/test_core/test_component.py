import reactpy
from reactpy.testing import DisplayFixture


def test_component_repr():
    @reactpy.component
    def MyComponent(a, *b, **c):
        pass

    mc1 = MyComponent(1, 2, 3, x=4, y=5)

    expected = f"MyComponent({id(mc1):02x}, a=1, b=(2, 3), c={{'x': 4, 'y': 5}})"
    assert repr(mc1) == expected

    # not enough args supplied to function
    assert repr(MyComponent()) == "MyComponent(...)"


async def test_simple_component():
    @reactpy.component
    def SimpleDiv():
        return reactpy.html.div()

    assert SimpleDiv().render() == {"tagName": "div"}


async def test_simple_parameterized_component():
    @reactpy.component
    def SimpleParamComponent(tag):
        return reactpy.vdom(tag)

    assert SimpleParamComponent("div").render() == {"tagName": "div"}


async def test_component_with_var_args():
    @reactpy.component
    def ComponentWithVarArgsAndKwargs(*args, **kwargs):
        return reactpy.html.div(kwargs, args)

    assert ComponentWithVarArgsAndKwargs("hello", "world", my_attr=1).render() == {
        "tagName": "div",
        "attributes": {"my_attr": 1},
        "children": ["hello", "world"],
    }


async def test_display_simple_hello_world(display: DisplayFixture):
    @reactpy.component
    def Hello():
        return reactpy.html.p({"id": "hello"}, ["Hello World"])

    await display.show(Hello)

    await display.page.wait_for_selector("#hello")


async def test_pre_tags_are_rendered_correctly(display: DisplayFixture):
    @reactpy.component
    def PreFormatted():
        return reactpy.html.pre(
            {"id": "pre-form-test"},
            reactpy.html.span("this", reactpy.html.span("is"), "some"),
            "pre-formatted",
            " text",
        )

    await display.show(PreFormatted)

    pre = await display.page.wait_for_selector("#pre-form-test")

    assert (
        await pre.evaluate("node => node.innerHTML")
    ) == "<span>this<span>is</span>some</span>pre-formatted text"
