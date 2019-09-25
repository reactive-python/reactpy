import codecs
import traceback
import encodings
import traceback
from io import StringIO
from encodings import utf_8
from typing import Any, Tuple, Optional

from .transpile import transpile_html_templates


def idom_decode(input: bytes, errors: str = "strict") -> Tuple[str, int]:
    value = transpile_html_templates(utf_8.decode(input, errors)[0])
    return value, len(value)


class IdomIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input: bytes, final: bool = False) -> str:
        try:
            self.buffer += input
            if final:
                buff = self.buffer
                self.buffer = b""
                value, _ = idom_decode(buff)
                return super().decode(value.encode("utf-8"), final=True)
            else:
                return ""
        except Exception:
            traceback.print_exc()
            raise


class IdomStreamReader(utf_8.StreamReader):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        try:
            codecs.StreamReader.__init__(self, *args, **kwargs)
            self.stream: StringIO = StringIO(
                transpile_html_templates(self.stream.read())
            )
        except Exception:
            traceback.print_exc()
            raise


def search_function(encoding: str) -> Optional[codecs.CodecInfo]:
    if encoding != "idom":
        return None

    # Assume utf8 encoding
    utf8 = encodings.search_function("utf8")

    return codecs.CodecInfo(
        name="idom",
        encode=utf8.encode,
        decode=idom_decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=IdomIncrementalDecoder,
        streamreader=IdomStreamReader,
        streamwriter=utf8.streamwriter,
    )


# see: https://github.com/python/typeshed/issues/3262
codecs.register(search_function)  # type: ignore


try:
    from ipykernel.ipkernel import IPythonKernel
except ImportError:
    pass
else:

    def register_to_ipykernel(kernel: Optional["IPythonKernel"] = None) -> None:
        if kernel is None:
            kernel = IPythonKernel.instance()

        original = kernel.shell.run_cell

        def wrapper(raw_cell: str, *args: Any, **kwargs: Any) -> Any:
            return original(transpile_html_templates(raw_cell), *args, **kwargs)

        kernel.shell.run_cell = wrapper

    if IPythonKernel.initialized():
        register_to_ipykernel()
    else:
        original = IPythonKernel.instance

        def wrapper(*args: Any, **kwargs: Any) -> IPythonKernel:
            inst = original(*args, **kwargs)
            register_to_ipykernel(inst)
            return inst

        IPythonKernel.instance = wrapper
