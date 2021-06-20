FAQ
===

See our `Discussion Forum <https://github.com/idom-team/idom/discussions>`__ for more
questions and answers.


Do UI components run server-side?
---------------------------------

No. The layout is constructed, and components are executed, server-side in Python. Only
rendering occurs client-side. This means you can access files, databases, and all your
favorite Python packages with IDOM.


Does IDOM transpile Python to Javascript?
-----------------------------------------

No. As in the answer to :ref:`Do UI components run server-side?`, IDOM runs almost
everything server-side and in Python. This was an explicit design choice to keep things
simple and one which allows you to do everything you normally would in Python.


Does IDOM support any React component?
--------------------------------------

If you use :ref:`Dynamically Loaded Components`, then the answer is no. Only components
whose props are JSON serializable, or which expect basic callback functions similar to
those of standard event handlers (e.g. ``onClick``) will operate as expected.

However, if you import a :ref:`Custom Javascript Component <Custom Javascript Components>`
then, so long as the bundle has be defined appropriately, any component can be made to
work, even those that don't rely on React.


How does IDOM communicate with the client?
------------------------------------------

IDOM sends diffs of a Virtual Document Object Model (:ref:`VDOM <VDOM Mimetype>`) to the
client. For more details, see the description in
`this article <https://ryanmorshead.com/articles/2021/idom-react-but-its-python/article/#virtual-document-object-model>`__.


Can I use Javascript components from a CDN?
-------------------------------------------

Yes, but with some restrictions:

1. The Javascript in question must be distributed as an ECMAScript Module
   (`ESM <https://hacks.mozilla.org/2018/03/es-modules-a-cartoon-deep-dive/>`__)
2. The module must export the :ref:`required interface <Custom Javascript Components>`.

These restrictions apply because the Javascript from the CDN must be able to run
natively in the browser and the module must be able to run in isolation from the main
application.

See :ref:`Distributing Javascript via CDN_` for more info.


What props can I pass to Javascript components?
-----------------------------------------------

You can only pass JSON serializable props to components implemented in Javascript. It is
possible to create a :ref:`Custom Javascript Component <Custom Javascript Components>`
which undestands how to deserialise JSON data into native Javascript objects though.
