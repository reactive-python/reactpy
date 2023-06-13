from reactpy import component, hooks


@component
def use_counting_hook(initial):

    number, set_number = hooks.use_state(initial)

    def increment():
        set_number(number + 1)

    def decrement():
        set_number(number - 1)

    return [number, increment, decrement]