State as a Snapshot
===================

While you can read state variables like you might normally in Python, as we
:ref:`learned earlier <Components with State>`, assigning to them is somewhat different.
When you use a state setter to update a component, instead of modifying your handle to
its corresponding state variable, a re-render is triggered. Only after that next render
begins will things change.
