from reactpy import component, html

# start


@component
def article_card():
    # Children are positional. The first argument is attributes only if it is a
    # plain dict, which is why a leading `None` is needed when there are no
    # attributes but the first child could look like one.
    return html.article(
        {"class": "card"},
        html.h2("Naming rules"),
        html.p(
            html.em("html.del_"),
            " is ",
            html.code("<del>"),
            ", ",
            html.code("html.data_table"),
            " is ",
            html.code("<data-table>"),
            ".",
        ),
        html.ul(
            None,
            [html.li({"key": word}, word) for word in ("class", "style", "key")],
        ),
        html.hr(),
        html.p({"class": "muted"}, "Void tags take no children."),
    )


@component
def app():
    return html.main(None, article_card(), html.br(), html.p("End of page."))
