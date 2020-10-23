import idom


def test_element_repr():
    @idom.element
    def MyElement(a, *b, **c):
        pass

    m_e = MyElement(1, 2, 3, x=4, y=5)

    expected = f"MyElement({hex(id(m_e))}, a=1, b=(2, 3), c={{'x': 4, 'y': 5}})"
    assert repr(m_e) == expected


async def test_simple_element():
    @idom.element
    def SimpleDiv():
        return idom.html.div()

    assert SimpleDiv().render() == {"tagName": "div"}


async def test_simple_parameterized_element():
    @idom.element
    def SimpleParamElement(tag):
        return idom.vdom(tag)

    assert SimpleParamElement("div").render() == {"tagName": "div"}


async def test_element_with_var_args():
    @idom.element
    def ElementWithVarArgsAndKwargs(*args, **kwargs):
        return idom.html.div(kwargs, args)

    assert ElementWithVarArgsAndKwargs("hello", "world", myAttr=1).render() == {
        "tagName": "div",
        "attributes": {"myAttr": 1},
        "children": ["hello", "world"],
    }


def test_display_simple_hello_world(driver, display):
    @idom.element
    def Hello():
        return idom.html.p({"id": "hello"}, ["Hello World"])

    display(Hello)

    assert driver.find_element_by_id("hello")


def test_pre_tags_are_rendered_correctly(driver, display):
    @idom.element
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
