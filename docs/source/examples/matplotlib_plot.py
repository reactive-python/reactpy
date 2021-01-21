from io import BytesIO

import matplotlib.pyplot as plt

import idom
from idom.widgets.html import image


@idom.component
def PolynomialPlot():
    coefficients, set_coefficients = idom.hooks.use_state([0])

    x = [n for n in linspace(-1, 1, 50)]
    y = [polynomial(value, coefficients) for value in x]

    return idom.html.div(
        plot(f"{len(coefficients)} Term Polynomial", x, y),
        ExpandableNumberInputs(coefficients, set_coefficients),
    )


@idom.component
def ExpandableNumberInputs(values, set_values):
    inputs = []
    for i in range(len(values)):

        def set_value_at_index(event, index=i):
            new_value = float(event["value"] or 0)
            set_values(values[:index] + [new_value] + values[index + 1 :])

        inputs.append(poly_coef_input(i, set_value_at_index))

    def add_input():
        set_values(values + [0])

    def del_input():
        set_values(values[:-1])

    return idom.html.div(
        idom.html.div(
            "add/remove term:",
            idom.html.button({"onClick": lambda event: add_input()}, "+"),
            idom.html.button({"onClick": lambda event: del_input()}, "-"),
        ),
        inputs,
    )


def plot(title, x, y):
    fig, axes = plt.subplots()
    axes.plot(x, y)
    axes.set_title(title)
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    return image("png", buffer.getvalue())


def poly_coef_input(index, callback):
    return idom.html.div(
        {"style": {"margin-top": "5px"}},
        idom.html.label(
            "C",
            idom.html.sub(index),
            " × X",
            idom.html.sup(index),
        ),
        idom.html.input(
            {
                "type": "number",
                "onChange": callback,
            },
        ),
    )


def polynomial(x, coefficients):
    return sum(c * (x ** i) for i, c in enumerate(coefficients))


def linspace(start, stop, n):
    if n == 1:
        yield stop
        return
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i


idom.run(PolynomialPlot)
