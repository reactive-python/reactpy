from reactpy import hooks


# start
answer, set_answer = hooks.use_state("")
error, set_error = hooks.use_state(None)
status, set_status = hooks.use_state("typing") # 'typing', 'submitting', or 'success'