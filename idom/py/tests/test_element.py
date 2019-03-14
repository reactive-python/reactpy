import idom


def test_element_default_state():
    ref = idom.Ref()

    @idom.element
    def element(self, x, y=1):
        pass

    e = element()

    # arguments in default 
    assert e.state == {"y": 1}
