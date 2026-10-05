from reactpy import component, html

# start

# Any name is a tag: underscores become dashes, so this is <user-badge>.
user_badge = html.user_badge


@component
def profile(name, role):
    return html.section(
        {"class": "profile", "data-role": role},
        html.h2(name),
        # A plain string is a text child; an attribute dict is always first.
        html.p({"class": "muted"}, "Signed in as ", html.strong(name)),
        user_badge({"role": role, "label": role.title()}),
        html.footer(
            html.small(
                {"style": {"font-size": "12px", "color": "#666"}},
                "Last seen today",
            )
        ),
    )


@component
def app():
    return html.main(
        None,
        html.h1("Accounts"),
        profile("Ada", "admin"),
        profile("Linus", "viewer"),
    )
