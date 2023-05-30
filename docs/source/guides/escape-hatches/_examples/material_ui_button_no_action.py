from reactpy import component, run, web

mui = web.module_from_template(
    "react@^17.0.0",
    "@material-ui/core@4.12.4",
    fallback="⌛",
)
Button = web.export(mui, "Button")


@component
def HelloWorld():
    return Button({"color": "primary", "variant": "contained"}, "Hello World!")


run(HelloWorld)
