Rules of Hooks
==============

Hooks are just normal Python functions, but there's a bit of magic to them, and in order
for that magic to work you've got to follow two rules. Thankfully we supply a
:ref:`Flake8 Plugin` to help enforce them.


Only call outside flow controls
-------------------------------

**Don't call hooks inside loops, conditions, or nested functions.** Instead you must
always call hooks at the top level of your functions. By adhering to this rule you
ensure that hooks are always called in the exact same order. This fact is what allows
IDOM to preserve the state of hooks between multiple calls to ``useState`` and
``useEffect`` calls.


Only call in IDOM functions
---------------------------

**Don't call hooks from regular Python functions.** Instead you should:

- ✅ Call Hooks from a component's render function.

- ✅ Call Hooks from another custom hook

Following this rule ensures stateful logic for IDOM component is always clearly
separated from the rest of your codebase.


Flake8 Plugin
-------------

We provide a Flake8 plugin called `flake8-idom-hooks <Flake8 Linter Plugin>`_ that helps
to enforce the two rules described above. You can ``pip`` install it directly, or with
the ``lint`` extra for IDOM:

.. code-block:: bash

    pip install flake8-idom-hooks

Once installed running, ``flake8`` on your code will start catching errors. For example:

.. code-block:: bash

    flake8 my_idom_components.py

Might produce something like the following output:

.. code-block:: text

    ./my_idom_components:10:8 ROH102 hook 'use_effect' used inside if statement
    ./my_idom_components:23:4 ROH102 hook 'use_state' used outside component or hook definition

See the Flake8 docs for
`more info <https://flake8.pycqa.org/en/latest/user/configuration.html>`__.

.. links
.. =====

.. _React Hooks: https://reactjs.org/docs/hooks-reference.html
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
.. _memoization: https://en.wikipedia.org/wiki/Memoization
.. _Flake8 Linter Plugin: https://github.com/idom-team/flake8-idom-hooks
