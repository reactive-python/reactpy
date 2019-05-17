import idom


def test_simple_hello_world(webdriver, display):
    @idom.element
    async def Hello(self):
        return idom.html.p("Hello World", id="hello")

    display(Hello)

    assert webdriver.find_element_by_id("hello")


def test_simple_click_event(webdriver, display, implicit_wait):
    clicked = idom.Var(False)

    @idom.element
    async def Button(self):
        events = idom.Events()

        @events.on("Click")
        async def on_click():
            clicked.set(True)
            self.update()

        if not clicked.get():
            return idom.html.button("Click Me!", eventHandlers=events, id="click")
        else:
            return idom.html.p("Success", id="complete")

    display(Button)

    button = webdriver.find_element_by_id("click")
    button.click()
    webdriver.find_element_by_id("complete")

    assert clicked.get()
