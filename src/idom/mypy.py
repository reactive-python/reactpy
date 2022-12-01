from __future__ import annotations

from typing import Any, Callable, Final

from mypy.errorcodes import ErrorCode
from mypy.nodes import ArgKind
from mypy.plugin import FunctionContext, Plugin
from mypy.types import CallableType, Instance, Type


KEY_IN_RENDER_FUNC_ERROR: Final = ErrorCode(
    "idom-key-in-render-func",
    "Component render function has reserved 'key' parameter",
    "IDOM",
)

NO_STAR_ARGS_ERROR: Final = ErrorCode(
    "idom-no-star-args",
    "Children were passed using *args instead of as a list or tuple",
    "IDOM",
)


class MypyPlugin(Plugin):
    """MyPy plugin for IDOM"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._idom_component_function_names: set[str] = set()

    def get_function_hook(self, fullname: str) -> Callable[[FunctionContext], Type]:
        if fullname == "idom.core.component.component":
            return self._idom_component_decorator_hook
        elif fullname in self._idom_component_function_names:
            return self._idom_component_function_hook
        return super().get_function_hook(fullname)

    def _idom_component_function_hook(self, ctx: FunctionContext) -> CallableType:
        if any(ArgKind.ARG_STAR in arg_kinds for arg_kinds in ctx.arg_kinds):
            ctx.api.msg.fail(
                "Cannot pass variable number of children to component using *args",
                ctx.context,
                code=NO_STAR_ARGS_ERROR,
            )
            ctx.api.msg.note(
                "You can pass a sequence of children directly to a component. That is, "
                "`example(*children)` will be treated the same as `example(children)`. "
                'Bear in mind that all children in such a sequence must have a  "key" '
                "that uniquely identifies each child amongst its siblings.",
                ctx.context,
                code=NO_STAR_ARGS_ERROR,
            )
        return ctx.default_return_type

    def _idom_component_decorator_hook(self, ctx: FunctionContext) -> CallableType:
        if not ctx.arg_types or not ctx.arg_types[0]:
            return ctx.default_return_type

        render_func: CallableType = ctx.arg_types[0][0]

        if render_func.definition:
            self._idom_component_function_names.add(render_func.definition.fullname)

        if render_func.argument_by_name("key") is not None:
            ctx.api.msg.fail(
                "Component render function has reserved 'key' parameter",
                ctx.context,
                code=KEY_IN_RENDER_FUNC_ERROR,
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
