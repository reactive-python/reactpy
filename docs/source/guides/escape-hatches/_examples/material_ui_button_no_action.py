import idom


mui = idom.web.module_from_template("react", "@material-ui/core@^5.0", fallback="⌛")
Button = idom.web.export(mui, "Button")

idom.run(
    idom.component(
        lambda: Button({"color": "primary", "variant": "contained"}, "Hello World!")
    )
)
