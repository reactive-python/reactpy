from functools import wraps


import idom


class HookCatcher:

    current: idom.hooks.LifeCycleHook

    def capture(self, render_function):
        @wraps(render_function)
        async def wrapper(*args, **kwargs):
            self.current = idom.hooks.current_hook()
            return await render_function(*args, **kwargs)

        return wrapper

    def schedule_render(self) -> None:
        self.current.schedule_render()
