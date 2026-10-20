from reactpy import component, use_state


# start
@component
def my_button():
    count, set_count = use_state(0)
    # ...
