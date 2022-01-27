from random import random

from idom import component, hooks, html, run


@component
def Demo():
    h = hooks.current_hook()
    print("render")
    return html.div(
        html.button({"onClick": lambda event: h.schedule_render()}, "re-render"),
        HasState(),
        key=str(random()),
    )


@component
def HasState():
    state = hooks.use_state(random)[0]
    return html.p(state)


run(Demo)
