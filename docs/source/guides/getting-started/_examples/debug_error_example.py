from reactpy import component, html, run


@component
def App():
    return html.div(GoodComponent(), BadComponent())


@component
def GoodComponent():
    return html.p("This component rendered successfuly")


@component
def BadComponent():
    raise RuntimeError("This component raised an error")


run(App)
