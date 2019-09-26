import codecs
import traceback
import encodings
import traceback
from io import StringIO
from encodings import utf_8
from typing import Any, Tuple, Optional, Type

from .transpile import transpile_html_templates


def idom_decode(input: bytes, errors: str = "strict") -> Tuple[str, int]:
    value = transpile_html_templates(utf_8.decode(input, errors)[0])
    return value, len(value)


class IdomIncrementalDecoder(codecs.IncrementalDecoder):
    def __init__(self, errors: str) -> None:
        super().__init__(errors)
        self.reset()

    def reset(self) -> None:
        self.buffer = b""

    def getstate(self) -> Tuple[bytes, int]:
        return self.buffer, 0

    def setstate(self, state: Tuple[bytes, int]) -> None:
        self.buffer, _ = state

    def decode(self, input: bytes, final: bool = False) -> str:
        try:
            self.buffer += input
            if final:
                buff = self.buffer
                self.buffer = b""
                result, _ = idom_decode(buff, self.errors)
            else:
                result = ""
            return result
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
    if encoding != "html":
        return None

    # Assume utf8 encoding
    utf8 = encodings.search_function("utf8")

    return codecs.CodecInfo(
        name="html",
        encode=utf8.encode,
        decode=idom_decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=IdomIncrementalDecoder,
        streamreader=IdomStreamReader,
        streamwriter=utf8.streamwriter,
    )


try:
    codecs.getdecoder("html")
except LookupError:
    # see: https://github.com/python/typeshed/issues/3262
    codecs.register(search_function)  # type: ignore


try:
    from IPython.core.interactiveshell import InteractiveShell
except ImportError:
    pass
else:
    # hack to register the transpiler to the IPython and Jupyter interactive shell

    from IPython.core.interactiveshell import ExecutionInfo, ExecutionResult

    def register_to_ipython_shell(shell: Optional[InteractiveShell] = None) -> None:
        shell_inst: InteractiveShell = shell or InteractiveShell.instance()

        original = shell_inst.run_cell

        def wrapper(
            raw_cell: str,
            store_history: bool = False,
            silent: bool = False,
            shell_futures: bool = True,
        ) -> ExecutionResult:
            try:
                transpiled_cell = transpile_html_templates(raw_cell)
            except Exception as error:
                info = ExecutionInfo(raw_cell, store_history, silent, shell_futures)
                result = ExecutionResult(info)
                result.error_before_exec = error
                shell_inst.showtraceback()
                return result
            else:
                return original(transpiled_cell, store_history, silent, shell_futures)

        shell_inst.run_cell = wrapper

    if InteractiveShell.initialized():
        register_to_ipython_shell()
    else:
        original = InteractiveShell.instance.__func__

        def wrapper(
            cls: Type[InteractiveShell], *args: Any, **kwargs: Any
        ) -> InteractiveShell:
            inst = original(cls, *args, **kwargs)
            register_to_ipython_shell(inst)
            return inst

        InteractiveShell.instance = classmethod(wrapper)
