import reactpy

mui = reactpy.web.module_from_template("react", "@material-ui/core@^5.0", fallback="⌛")
Switch = reactpy.web.export(mui, "Switch")


@reactpy.component
def DayNightSwitch():
    checked, set_checked = reactpy.hooks.use_state(False)

    return reactpy.html.div(
        Switch(
            {
                "checked": checked,
                "onChange": lambda event, checked: set_checked(checked),
            }
        ),
        "🌞" if checked else "🌚",
    )


reactpy.run(DayNightSwitch)
