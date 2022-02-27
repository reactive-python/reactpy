import idom


mui = idom.web.module_from_template("react", "@material-ui/core@^5.0", fallback="⌛")
Switch = idom.web.export(mui, "Switch")


@idom.component
def DayNightSwitch():
    checked, set_checked = idom.hooks.use_state(False)

    return idom.html.div(
        Switch(
            {
                "checked": checked,
                "onChange": lambda event, checked: set_checked(checked),
            }
        ),
        "🌞" if checked else "🌚",
    )


idom.run(DayNightSwitch)
