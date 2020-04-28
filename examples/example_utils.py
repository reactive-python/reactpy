import os
from IPython import display
from typing import Mapping, Any, Optional


def example_server_url(host: str, port: int) -> str:
    localhost_idom_path = f"http://{host}:{port}"
    jupyterhub_idom_path = path_to_jupyterhub_proxy(port)
    return jupyterhub_idom_path or localhost_idom_path


def path_to_jupyterhub_proxy(port: int) -> Optional[str]:
    """If running on Jupyterhub return the path from the host's root to a proxy server

    This is used when examples are running on mybinder.org or in a container created by
    jupyter-repo2docker. For this to work a ``jupyter_server_proxy`` must have been
    instantiated.
    """
    if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
        url = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
        return f"{url}/proxy/{port}"
    elif "JUPYTER_SERVER_URL" in os.environ:
        return f"{os.environ['JUPYTER_SERVER_URL']}/proxy/{port}"
    else:
        return None


def display_href(href: str) -> None:
    display.display_html(f"<a href='{href}' target='_blank'>{href}</a>", raw=True)
    return None


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
