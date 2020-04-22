import os
from typing import Mapping, Any, Optional


def example_uri_root(protocol: str, port: int) -> str:
    """Returns the IDOM root URI for example notebooks

    When examples are running on mybinder.org or in a container created by
    jupyter-repo2docker this is not simply "localhost" or "127.0.0.1".
    Instead we use a route produced by ``jupyter_server_proxy`` instead.
    """
    if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
        auth = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
        return "%s/proxy/%s" % (auth, port)
    elif "JUPYTER_SERVER_URL" in os.environ:
        return "%s/proxy/%s" % (os.environ["JUPYTER_SERVER_URL"], port)
    else:
        return "%s://127.0.0.1:%s" % (protocol, port)


def is_on_jupyterhub() -> bool:
    return (
        "JUPYTER_SERVER_URL" in os.environ
        or "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ
    )


class HtmlLink:
    def __init__(self, href: str, text: Optional[str] = None):
        self.href, self.text = href, text

    def __str__(self) -> str:
        return self.href

    def _repr_html_(self) -> str:
        return f"<a href='{self.href}' target='_blank'>{self.text or self.href}</a>"


def pretty_dict_string(
    value: Mapping[Any, Any], indent: int = 1, depth: int = 0
) -> str:
    """Simple function for printing out nested mappings."""

    last_indent = " " * (indent * depth)
    depth += 1
    this_indent = " " * (indent * depth)

    if isinstance(value, Mapping):
        s = "{\n"

        for k in value:
            v = value[k]
            s += this_indent
            s += "%r: %s,\n" % (k, pretty_dict_string(v, indent, depth + 1))

        s += last_indent + "}"
        return s
    else:
        return repr(value)
