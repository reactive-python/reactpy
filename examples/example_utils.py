import os
from collections.abc import Mapping


def localhost(protocol, port):
    """Returns the host URL.

    When examples are running on mybinder.org or in a container created by
    jupyter-repo2docker this is not simply "localhost" or "127.0.0.1".
    Instead we use a route produced by ``jupyter_server_proxy`` instead.
    """
    if "JUPYTERHUB_OAUTH_CALLBACK_URL" in os.environ:
        protocol += "s"
        form = protocol + "://hub.mybinder.org%s/proxy/%s"
        auth = os.environ["JUPYTERHUB_OAUTH_CALLBACK_URL"].rsplit("/", 1)[0]
        return form % (auth, port)
    elif "JUPYTER_SERVER_URL" in os.environ:
        return "%s/proxy/%s" % (os.environ["JUPYTER_SERVER_URL"], port)
    else:
        form = protocol + "://127.0.0.1:%s"
        return form % port


def pretty_dict_string(value, indent=1, depth=0):
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
