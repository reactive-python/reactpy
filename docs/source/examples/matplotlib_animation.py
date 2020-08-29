# import time
# import asyncio
# import random

# from matplotlib import pyplot as plt

# import idom


# @idom.element
# async def RandomWalk(self, timeout=20):
#     start = time.time()

#     x, y = [0] * 50, [0] * 50
#     plot = Plot(x, y)

#     mu_var, mu_inputs = linked_inputs(
#         "Mean", 0, "number", "range", min=-1, max=1, step=0.01
#     )
#     sigma_var, sigma_inputs = linked_inputs(
#         "Standard Deviation", 1, "number", "range", min=0, max=2, step=0.01
#     )

#     @self.animate(rate=0.5)
#     async def walk(stop):
#         x.pop(0)
#         x.append(x[-1] + 1)
#         y.pop(0)
#         diff = random.gauss(float(mu_var.get()), float(sigma_var.get()))
#         y.append(y[-1] + diff)
#         plot.update(x, y)

#         if (time.time() - start) > timeout:
#             stop()

#     style = idom.html.style(
#         [
#             """
#             .linked-inputs {margin-bottom: 20px}
#             .linked-inputs input {width: 48%;float: left}
#             .linked-inputs input + input {margin-left: 4%}
#             """
#         ]
#     )

#     async def restart(event):
#         self.update()

#     restart_button = idom.html.button({"onClick": restart}, "Run It Again ♻️")

#     return idom.html.div(
#         {"style": {"width": "60%"}},
#         [restart_button, style, plot, mu_inputs, sigma_inputs],
#     )


# @idom.element(run_in_executor=True)
# async def Plot(self, x, y):
#     fig, axes = plt.subplots()
#     axes.plot(x, y)
#     img = idom.Image("png")
#     fig.savefig(img.io, format="png")
#     plt.close(fig)
#     return img


# def linked_inputs(label, value, *types, **attributes):
#     var = idom.Var(value)

#     inputs = []
#     for tp in types:
#         inp = idom.Input(tp, value, attributes, cast=float)

#         @inp.events.on("change")
#         async def on_change(event, inp=inp):
#             for i in inputs:
#                 i.update(inp.value)
#             var.set(inp.value)

#         inputs.append(inp)

#     fs = idom.html.fieldset(
#         {"class": "linked-inputs"},
#         [idom.html.legend({"style": {"font-size": "medium"}}, label)],
#         inputs,
#     )

#     return var, fs


# display(RandomWalk)
