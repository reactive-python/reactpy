IDOM
====

.. toctree::
    :hidden:
    :caption: Tutorials

    tutorials/installation
    tutorials/breaking-down-an-example
    tutorials/handling-events
    tutorials/javascript-components

.. toctree::
    :hidden:
    :caption: Guides

    guides/simple-examples
    guides/making-a-game
    guides/matplotlib-plot
    guides/basic-dashboard
    guides/using-3rd-party-js
    guides/writing-your-own-js

.. toctree::
    :hidden:
    :caption: References

    references/life-cycle-hooks
    references/core-abstractions
    references/architectural-patterns
    references/user-apis
    references/specifications
    references/faq

.. toctree::
    :hidden:
    :caption: Development

    development/contributing
    development/developer-guide
    references/developer-apis
    development/changelog
    development/roadmap

.. toctree::
    :hidden:
    :caption: Resources

    Source Code <https://github.com/idom-team/idom>
    Community <https://github.com/idom-team/idom/discussions>
    Issues <https://github.com/idom-team/idom/issues>

A package for building responsive user interfaces in pure Python.

- Create full stack applications without writing a single line of Javascript.
- Rapidly and easily develop :ref:`interactive data dashboards <Simple Dashboard>`.
- Use many existing Javascript packages without any extra work.
- Leverage time-tested :ref:`declarative <Declarative Components>` design patterns
  inspired by `ReactJS <https://reactjs.org>`__.
- Write :ref:`custom Javascript components` when you need client-side performance.
- Is :ref:`ecosystem independent <ecosystem independence>` - works with
  `Jupyter <https://github.com/idom-team/idom-jupyter>`__,
  `Dash <https://github.com/idom-team/idom-dash>`__,
  `Django <https://github.com/idom-team/django-idom>`__, and more.
- Add to existing applications with the
  `Javascript client <https://github.com/idom-team/idom/tree/main/src/client>`__.

.. grid:: 1 1 2 2
    :gutter: 1

    .. grid-item::

        .. grid:: 1 1 1 1
            :gutter: 1

            .. grid-item-card::

                .. interactive-widget:: pigeon_maps
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: network_graph
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: snake_game
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: slideshow
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: audio_player
                    :no-activate-button:

    .. grid-item::

        .. grid:: 1 1 1 1
            :gutter: 1

            .. grid-item-card::

                .. interactive-widget:: simple_dashboard
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: matplotlib_plot
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: material_ui_button_on_click
                    :no-activate-button:

            .. grid-item-card::

                .. interactive-widget:: todo
                    :no-activate-button:
