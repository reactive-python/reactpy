.. testcode::

    from reactpy import html


HTML Attributes
===============

In ReactPy, HTML attributes are specified using snake_case instead of dash-separated
words. For example, ``tabindex`` and ``margin-left`` become ``tab_index`` and
``margin_left`` respectively.


Noteable Attributes
-------------------

Some attributes in ReactPy are renamed, have special meaning, or are used differently
than in HTML.

``style``
.........

As mentioned above, instead of using a string to specify the ``style`` attribute, we use
a dictionary to describe the CSS properties we want to apply to an element. For example,
the following HTML:

.. code-block:: html

    <div style="width: 50%; margin-left: 25%;">
        <h1 style="margin-top: 0px;">My Todo List</h1>
        <ul>
            <li>Build a cool new app</li>
            <li>Share it with the world!</li>
        </ul>
    </div>

Would be written in ReactPy as:

.. testcode::

    html.div(
        {
            "style": {
                "width": "50%",
                "margin_left": "25%",
            },
        },
        html.h1(
            {
                "style": {
                    "margin_top": "0px",
                },
            },
            "My Todo List",
        ),
        html.ul(
            html.li("Build a cool new app"),
            html.li("Share it with the world!"),
        ),
    )

``class`` vs ``class_name``
...........................

In HTML, the ``class`` attribute is used to specify a CSS class for an element. In
ReactPy, this attribute is renamed to ``class_name`` to avoid conflicting with the
``class`` keyword in Python. For example, the following HTML:

.. code-block:: html

    <div class="container">
        <h1 class="title">My Todo List</h1>
        <ul class="list">
            <li class="item">Build a cool new app</li>
            <li class="item">Share it with the world!</li>
        </ul>
    </div>

Would be written in ReactPy as:

.. testcode::

    html.div(
        {"class_name": "container"},
        html.h1({"class_name": "title"}, "My Todo List"),
        html.ul(
            {"class_name": "list"},
            html.li({"class_name": "item"}, "Build a cool new app"),
            html.li({"class_name": "item"}, "Share it with the world!"),
        ),
    )

``for`` vs ``html_for``
.......................

In HTML, the ``for`` attribute is used to specify the ``id`` of the element it's
associated with. In ReactPy, this attribute is renamed to ``html_for`` to avoid
conflicting with the ``for`` keyword in Python. For example, the following HTML:

.. code-block:: html

    <div>
        <label for="todo">Todo:</label>
        <input id="todo" type="text" />
    </div>

Would be written in ReactPy as:

.. testcode::

    html.div(
        html.label({"html_for": "todo"}, "Todo:"),
        html.input({"id": "todo", "type": "text"}),
    )

``dangerously_set_inner_HTML``
..............................

This is used to set the ``innerHTML`` property of an element and should be provided a
dictionary with a single key ``__html`` whose value is the HTML to be set. It should be
used with **extreme caution** as it can lead to XSS attacks if the HTML inside isn't
trusted (for example if it comes from user input).


All Attributes
--------------

`access_key <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/accesskey>`__
  A string. Specifies a keyboard shortcut for the element. Not generally recommended.

`aria_* <https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes>`__
  ARIA attributes let you specify the accessibility tree information for this element.
  See ARIA attributes for a complete reference. In ReactPr, all ARIA attribute names are
  exactly the same as in HTML.

`auto_capitalize <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/autocapitalize>`__
  A string. Specifies whether and how the user input should be capitalized.

`content_editable <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/contenteditable>`__
  A boolean. If true, the browser lets the user edit the rendered element directly. This
  is used to implement rich text input libraries like Lexical. ReactPr warns if you try
  to pass children to an element with ``content_editable = True`` because ReactPy will
  not be able to update its content after user edits.

`data_* <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/data-*>`__
  Data attributes let you attach some string data to the element, for example
  data-fruit="banana". In ReactPy, they are not commonly used because you would usually
  read data from props or state instead.

`dir <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/dir>`__
  Either ``"ltr"`` or ``"rtl"``. Specifies the text direction of the element.

`draggable <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/draggable>`__
  A boolean. Specifies whether the element is draggable. Part of HTML Drag and Drop API.

`enter_key_hint <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/enterkeyhint>`__
  A string. Specifies which action to present for the enter key on virtual keyboards.

`hidden <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/hidden>`__
  A boolean or a string. Specifies whether the element should be hidden.

- `id <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/id>`__:
  A string. Specifies a unique identifier for this element, which can be used to find it
  later or connect it with other elements. Generate it with useId to avoid clashes
  between multiple instances of the same component.

`is <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script#attr-is>`__
  A string. If specified, the component will behave like a custom element.

`input_mode <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/inputmode>`__
  A string. Specifies what kind of keyboard to display (for example, text, number, or telephone).

`item_prop <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/itemprop>`__
  A string. Specifies which property the element represents for structured data crawlers.

`lang <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/lang>`__
  A string. Specifies the language of the element.

`role <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/role>`__
  A string. Specifies the element role explicitly for assistive technologies.

`slot <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/slot>`__
  A string. Specifies the slot name when using shadow DOM. In ReactPy, an equivalent
  pattern is typically achieved by passing JSX as props, for example
  ``<Layout left={<Sidebar />} right={<Content />} />``.

`spell_check <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/spellcheck>`__
  A boolean or null. If explicitly set to true or false, enables or disables spellchecking.

`tab_index <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/tabindex>`__
  A number. Overrides the default Tab button behavior. Avoid using values other than -1 and 0.

`title <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/title>`__
  A string. Specifies the tooltip text for the element.

`translate <https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/translate>`__
  Either 'yes' or 'no'. Passing 'no' excludes the element content from being translated.
