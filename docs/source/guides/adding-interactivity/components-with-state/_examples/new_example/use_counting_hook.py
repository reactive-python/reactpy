from reactpy import hooks

def reducer(count, action):
    if action == "increment":
        return count + 1
    elif action == "decrement":
        return count - 1
    elif action == "reset":
        return 0
    else:
        msg = f"Unknown action '{action}'"
        raise ValueError(msg)

def use_counting_hook(initial_value=0):
    return hooks.use_reducer(reducer, initial_value)