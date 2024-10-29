from reactpy import hooks

# start
is_empty, set_is_empty = hooks.use_state(True)
is_typing, set_is_typing = hooks.use_state(False)
is_submitting, set_is_submitting = hooks.use_state(False)
is_success, set_is_success = hooks.use_state(False)
is_error, set_is_error = hooks.use_state(False)
