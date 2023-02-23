from reactpy.core.hooks import current_hook, use_state


def use_force_render():
    return current_hook().schedule_render


def use_toggle(init=False):
    state, set_state = use_state(init)
    return state, lambda: set_state(lambda old: not old)


def use_counter(initial_value):
    state, set_state = use_state(initial_value)
    return state, lambda: set_state(lambda old: old + 1)
