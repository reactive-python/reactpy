import idom


@idom.component
def Demo():
    return idom.vdom("", idom.html.h1("hello"))


idom.run(Demo)
