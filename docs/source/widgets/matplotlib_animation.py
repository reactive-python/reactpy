import time
import asyncio
import random
import gc

from matplotlib import pyplot as plt

import idom

from _utils import click_to_start


@click_to_start
@idom.element
async def RandomWalk(self):
    x, y = [0] * 50, [0] * 50
    plot = Plot(x, y)

    mu_var, mu_inputs = linked_inputs(
        "Mean", 0, "number", "range", min=-1, max=1, step=0.01
    )
    sigma_var, sigma_inputs = linked_inputs(
        "Standard Deviation", 1, "number", "range", min=0, max=2, step=0.01
    )

    @self.animate(rate=0.5)
    async def walk(stop):
        x.pop(0)
        x.append(x[-1] + 1)
        y.pop(0)
        diff = random.gauss(float(mu_var.get()), float(sigma_var.get()))
        y.append(y[-1] + diff)
        plot.update(x, y)

    style = idom.html.style(
        [
            """
            .linked-inputs {margin-bottom: 20px}
            .linked-inputs input {width: 48%;float: left}
            .linked-inputs input + input {margin-left: 4%}
            """
        ]
    )

    return idom.html.div(
        {"style": {"width": "60%"}}, [style, plot, mu_inputs, sigma_inputs],
    )


@idom.element(run_in_executor=True)
async def Plot(self, x, y):
    fig, axes = plt.subplots()
    axes.plot(x, y)
    img = idom.Image("png")
    fig.savefig(img.io, format="png")
    plt.close(fig)
    # Figures are slow to be garbage collected so we
    # do a deep cleaning here to reduce memory usage
    gc.collect(2)
    return img


def linked_inputs(label, value, *types, **attributes):
    var = idom.Var(value)

    inputs = []
    for tp in types:
        inp = idom.Input(tp, value, attributes, cast=float)

        @inp.events.on("change")
        async def on_change(event, inp=inp):
            for i in inputs:
                i.update(inp.value)
            var.set(inp.value)

        inputs.append(inp)

    fs = idom.html.fieldset(
        {"class": "linked-inputs"},
        [idom.html.legend({"style": {"font-size": "medium"}}, label)],
        inputs,
    )

    return var, fs


display(RandomWalk)
