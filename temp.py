import idom


victory = idom.web.module_from_template("react", "victory-bar@35.4.0")
VictoryBar = idom.web.export(victory, "VictoryBar")


@idom.component
def Demo():
    return VictoryBar()


idom.run(Demo)
