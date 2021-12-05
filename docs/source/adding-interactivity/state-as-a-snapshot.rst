State as a Snapshot
===================

When you watch the user interfaces you build change as you interact with them, it's easy
to imagining that they do so because there's some bit of code that modifies the relevant
parts of the view directly. For example, you may think that when a user clicks a "Send"
button, there's code which reaches into the view and adds some text saying "Message
sent!":

.. image:: _static/direct-state-change.png

IDOM works a bit differently though. Previously, you'll have seen how, in order to
change the view you need to :ref:`"set state" <Introduction to use_state>`. Doing so
then triggers a re-render of the view.

.. image:: _static/idom-state-change.png

...

.. idom:: _examples/send_message
