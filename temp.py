from fastapi import FastAPI

from reactpy import html, web
from reactpy.backend.fastapi import configure

mui = web.module_from_template(
    "react",
    "@mui/x-date-pickers",
    fallback="please wait loading...",
)


# Create calendar with material ui
DatePicker = web.export(mui, "DatePicker")


def Mycalender():
    return html.div(
        DatePicker(
            {
                "label": "Basic date picker",
            },
            "my calender",
        ),
    )


app = FastAPI()
configure(app, Mycalender)
