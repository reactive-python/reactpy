import pytest

import idom


def test_component_repr():
    @idom.component
    def MyComponent(a, *b, **c):
        pass

    m_e = MyComponent(1, 2, 3, x=4, y=5)

    expected = f"MyComponent({hex(id(m_e))}, a=1, b=(2, 3), c={{'x': 4, 'y': 5}})"
    assert repr(m_e) == expected


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


def test_display_simple_hello_world(driver, display):
    @idom.component
    def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element_by_id("hello")


def test_pre_tags_are_rendered_correctly(driver, display):
    @idom.component
    def PreFormated():
        return idom.html.pre(
            {"id": "pre-form-test"},
            idom.html.span("this", idom.html.span("is"), "some"),
            "pre-formated",
            " text",
        )

    display(PreFormated)

    pre = driver.find_element_by_id("pre-form-test")

    assert (
        pre.get_attribute("innerHTML")
        == "<span>this<span>is</span>some</span>pre-formated text"
    )


def test_class_component(driver, display, driver_wait):
    class Counter(idom.AbstractComponent):
        def __init__(self):
            self.count = 0

        def render(self):
            return idom.html.button(
                {"onClick": lambda event: self._increment_count(), "id": "counter"},
                f"Clicked {self.count} times",
            )

        def _increment_count(self):
            self.count += 1
            self.schedule_render()

    display(Counter)

    client_counter = driver.find_element_by_id("counter")

    for i in range(5):
        driver_wait.until(
            lambda d: client_counter.get_attribute("innerHTML") == f"Clicked {i} times"
        )
        client_counter.click()


def test_class_component_has_no_hook():
    class MyComponent(idom.AbstractComponent):
        def render(self):
            ...

    component = MyComponent()

    with pytest.raises(RuntimeError, match="no hook"):
        component.schedule_render()
