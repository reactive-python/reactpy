from reactpy import hooks

# def reducer(count, action):
#     if action == "increment":
#         return count + 1
#     elif action == "decrement":
#         return count - 1
#     elif action == "reset":
#         return 0
#     else:
#         msg = f"Unknown action '{action}'"
#         raise ValueError(msg)

# def use_counting_hook(initial_value=0):
#     return hooks.use_reducer(reducer, initial_value)


def my_first_reactpy_hook(initial_value=0):
    def reducer(count, action):
        if action == "increment":
            return count + 1
        elif action == "decrement":
            return count - 1
        elif action == "reset":
            return initial_value
        else:
            msg = f"Unknown action '{action}'"
            raise ValueError(msg)

    count, dispatch = hooks.use_reducer(reducer, initial_value)

    def increment():
        dispatch("increment")

    def decrement():
        dispatch("decrement")

    def reset():
        dispatch("reset")

    return count, increment, decrement, reset