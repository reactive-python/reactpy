from typing import Callable, Final

from mypy.errorcodes import ErrorCode
from mypy.nodes import ArgKind
from mypy.plugin import FunctionContext, Plugin
from mypy.types import CallableType, Instance, Type


KEY_IN_RENDER_FUNC: Final = ErrorCode(
    "idom-key-in-render-func",
    "Component render function has reserved 'key' parameter",
    "IDOM",
)


class MypyPlugin(Plugin):
    """MyPy plugin for IDOM"""

    def get_function_hook(self, fullname: str) -> Callable[[FunctionContext], Type]:
        if fullname == "idom.core.component.component":
            return self.component_decorator_hook
        return super().get_function_hook(fullname)

    def component_decorator_hook(self, ctx: FunctionContext) -> CallableType:
        if not ctx.arg_types or not ctx.arg_types[0]:
            return ctx.default_return_type
        render_func: CallableType = ctx.arg_types[0][0]

        if render_func.argument_by_name("key") is not None:
            ctx.api.msg.fail(
                "Component render function has reserved 'key' parameter",
                ctx.context,
                code=KEY_IN_RENDER_FUNC,
            )
            return ctx.default_return_type

        component_symbol = self.lookup_fully_qualified("idom.core.component.Component")
        assert component_symbol is not None
        assert component_symbol.node is not None

        return render_func.copy_modified(
            arg_kinds=render_func.arg_kinds + [ArgKind.ARG_NAMED_OPT],
            arg_names=render_func.arg_names + ["key"],
            arg_types=render_func.arg_types + [ctx.api.named_generic_type("str", [])],
            ret_type=Instance(component_symbol.node, []),
        )


def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return MypyPlugin
