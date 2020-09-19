from idom.client.manage import install, installed


def install_doc_js_modules(show_spinner=True):
    to_install = {
        "@material-ui/core",
        "victory",
        "semantic-ui-react",
    }.difference(installed())
    if to_install:
        install(to_install, [], show_spinner=show_spinner)


if __name__ == "__main__":
    install_doc_js_modules()
