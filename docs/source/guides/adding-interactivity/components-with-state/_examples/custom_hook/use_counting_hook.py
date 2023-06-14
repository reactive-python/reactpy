from reactpy import hooks

# This is a custom hook that provides a counter functionality.
def use_counting_hook(initial_value=0):

    # The reducer function defines how the state (count) should be updated based on the action that is dispatched.
    def reducer(count, action):
        if action == "increment":
            # When the "increment" action is dispatched, the count is incremented.
            return count + 1
        elif action == "decrement":
            # When the "decrement" action is dispatched, the count is decremented.
            return count - 1
        elif action == "reset":
            # When the "reset" action is dispatched, the count is reset to the initial value.
            return initial_value
        else:
            # If an unknown action is dispatched, raise an error.
            msg = f"Unknown action '{action}'"
            raise ValueError(msg)

    # Use the use_reducer hook from reactpy. This hook provides the current state (count) and a dispatch function that can be used to update the state.
    count, dispatch = hooks.use_reducer(reducer, initial_value)

    # Define a function to increment the count by dispatching the "increment" action.
    def increment():
        dispatch("increment")

    # Define a function to decrement the count by dispatching the "decrement" action.
    def decrement():
        dispatch("decrement")

    # Define a function to reset the count by dispatching the "reset" action.
    def reset():
        dispatch("reset")

    # Return the current count along with the increment, decrement, and reset functions.
    # These can be used in a component to display and update the count.
    return count, increment, decrement, reset