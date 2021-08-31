import idom


@idom.component
def Test():
    raise ValueError("test message")


idom.run(Test, port=8000)
