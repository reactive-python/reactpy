from io import BytesIO

import matplotlib.pyplot as plt

import reactpy
from reactpy.widgets import image


@reactpy.component
def PolynomialPlot():
    coefficients, set_coefficients = reactpy.hooks.use_state([0])

    x = list(linspace(-1, 1, 50))
    y = [polynomial(value, coefficients) for value in x]

    return reactpy.html.div(
        plot(f"{len(coefficients)} Term Polynomial", x, y),
        ExpandableNumberInputs(coefficients, set_coefficients),
    )


@reactpy.component
def ExpandableNumberInputs(values, set_values):
    inputs = []
    for i in range(len(values)):

        def set_value_at_index(event, index=i):
            new_value = float(event["target"]["value"] or 0)
            set_values(values[:index] + [new_value] + values[index + 1 :])

        inputs.append(poly_coef_input(i + 1, set_value_at_index))

    def add_input():
        set_values([*values, 0])

    def del_input():
        set_values(values[:-1])

    return reactpy.html.div(
        reactpy.html.div(
            "add/remove term:",
            reactpy.html.button({"on_click": lambda event: add_input()}, "+"),
            reactpy.html.button({"on_click": lambda event: del_input()}, "-"),
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
    return reactpy.html.div(
        {"style": {"margin-top": "5px"}, "key": index},
        reactpy.html.label(
            "C",
            reactpy.html.sub(index),
            " x X",
            reactpy.html.sup(index),
        ),
        reactpy.html.input({"type": "number", "on_change": callback}),
    )


def polynomial(x, coefficients):
    return sum(c * (x ** (i + 1)) for i, c in enumerate(coefficients))


def linspace(start, stop, n):
    if n == 1:
        yield stop
        return
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i


reactpy.run(PolynomialPlot)
