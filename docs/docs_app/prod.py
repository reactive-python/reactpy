import os

from docs_app.app import make_app

app = make_app("docs_prod_app")


def main() -> None:
    app.run(
        host="0.0.0.0",  # noqa: S104
        port=int(os.environ.get("PORT", "5000")),
        workers=int(os.environ.get("WEB_CONCURRENCY", "1")),
        debug=bool(int(os.environ.get("DEBUG", "0"))),
    )
