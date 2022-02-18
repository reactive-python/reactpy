Changelog
=========

The IDOM team manages their short and long term plans with `GitHub Projects
<https://github.com/orgs/idom-team/projects/1>`__. If you have questions about what the
team are working on, or have feedback on how issues should be prioritized, feel free to
:discussion-type:`open up a discussion <question>`.


0.36.3
------

Misc bug fixes along with a minor improvement that allows components to return ``None``
to render nothing.

**Closed Issues**

- All child states wiped upon any child key change - :issue:`652`
- Allow NoneType returns within components - :issue:`538`

**Merged Pull Requests**

- fix #652 - :pull:`672`
- Fix 663 - :pull:`667`


0.36.2
------

Hot fix for newly introduced ``DeprecatedOption``:

- :commit:`c146dfb264cbc3d2256a62efdfe9ccf62c795b01`


0.36.1
------

Includes bug fixes and renames the configuration option ``IDOM_WED_MODULES_DIR`` to
``IDOM_WEB_MODULES_DIR`` with a corresponding deprecation warning.

**Closed Issues**

- Fix Key Error When Cleaning Up Event Handlers - :issue:`640`
- Update Script Tag Behavior - :issue:`628`

**Merged Pull Requests**

- mark old state as None if unmounting - :pull:`641`
- rename IDOM_WED_MODULES_DIR to IDOM_WEB_MODULES_DIR - :pull:`638`


0.36.0
------

This release includes an important fix for errors produced after :pull:`623` was merged.
In addition there is not a new ``http.script`` element which can behave similarly to a
standard HTML ``<script>`` or, if no attributes are given, operate similarly to an
effect. If no attributes are given, and when the script evaluates to a function, that
function will be called the first time it is mounted and any time the content of the
script is subsequently changed. If the function then returns another function, that
returned function will be called when the script is removed from the view, or just
before the content of the script changes.

**Closed Issues**

- State mismatch during component update - :issue:`629`
- Implement a script tag - :issue:`544`

**Pull Requests**

- make scripts behave more like normal html script element - :pull:`632`
- Fix state mismatch during component update - :pull:`631`
- implement script element - :pull:`617`


0.35.4
------

Keys for elements at the root of a component were not being tracked. Thus key changes
for elements at the root did not trigger unmounts.

**Closed Issues**

- Change Key of Parent Element Does Not Unmount Children - :issue:`622`

**Pull Requests**

- fix issue with key-based identity - :pull:`623`


0.35.3
------

As part of :pull:`614`, elements which changed type were not deeply unmounted. This
behavior is probably undesireable though since the state for children of the element
in question would persist (probably unexpectedly).

**Pull Requests**

- Always deeply unmount - :pull:`620`


0.35.2
------

This release includes several bug fixes. The most significant of which is the ability to
change the type of an element in the try (i.e. to and from being a component) without
getting an error. Originally the errors were introduced because it was though changing
element type would not be desireable. This was not the case though - swapping types
turns out to be quite common and useful.

**Closed Issues**

- Allow Children with the Same Key to Vary in Type - :issue:`613`
- Client Always Looks for Server at "/"  - :issue:`611`
- Web modules get double file extensions with v0.35.x - :issue:`605`

**Pull Requests**

- allow elements with the same key to change type - :pull:`614`
- make connection to websocket relative path - :pull:`612`
- fix double file extension - :pull:`606`


0.35.1
------

Re-add accidentally deleted ``py.typed`` file to distribution. See `PEP-561
<https://www.python.org/dev/peps/pep-0561/#packaging-type-information>`__ for info on
this marker file.


0.35.0
------

The highlight of this release is that the default :ref:`"key" <Organizing Items With
Keys>` of all elements will be their index amongst their neighbors. Previously this
behavior could be engaged by setting ``IDOM_FEATURE_INDEX_AS_DEFAULT_KEY=1`` when
running IDOM. In this release though, you will need to explicitely turn off this feature
(i.e. ``=0``) to return to the old behavior. With this change, some may notice
additional error logs which warn that:

.. code-block:: text

  Key not specified for child in list ...

This is saying is that an element or component which was created in a list does not have
a unique ``key``. For more information on how to mitigate this warning refer to the docs
on :ref:`Organizing Items With Keys`.

**Closed Issues**

- Support Starlette Server - :issue:`588`
- Fix unhandled case in module_from_template - :issue:`584`
- Hide "Children" within IDOM_DEBUG_MODE key warnings - :issue:`562`
- Bug in Element Key Identity - :issue:`556`
- Add iFrame to idom.html - :issue:`542`
- Create a use_linked_inputs widget instead of Input - :issue:`475`
- React warning from module_from_template - :issue:`440`
- Use Index as Default Key - :issue:`351`

**Pull Requests**

- add ``use_linked_inputs`` - :pull:`593`
- add starlette server implementation - :pull:`590`
- Log on web module replacement instead of error - :pull:`586`
- Make Index Default Key - :pull:`579`
- reduce log spam from missing keys in children - :pull:`564`
- fix bug in element key identity - :pull:`563`
- add more standard html elements - :pull:`554`


0.34.0
------

This release contains a variety of minor fixes and improvements which came out of
rewriting the documentation. The most significant of these changes is the remove of
target element attributes from the top-level of event data dictionaries. For example,
instead of being able to find the value of an input at ``event["value"]`` it will
instead be found at ``event["target"]["value"]``. For a short period we will issue a
:class:`DeprecationWarning` when target attributes are requested at the top-level of the
event dictionary. As part of this change we also add ``event["currentTarget"]`` and
``event["relatedTarget"]`` keys to the event dictionary as well as a
``event[some_target]["boundingClientRect"]`` where ``some_target`` may be ``"target"``,
``"currentTarget"`` or ``"relatedTarget"``.

**Closed Issues**

- Move target attributes to ``event['target']`` - :issue:`548`

**Pull Requests**

- Correctly Handle Target Event Data - :pull:`550`
- Clean up WS console logging - :pull:`522`
- automatically infer closure arguments - :pull:`520`
- Documentation Rewrite - :pull:`519`
- add option to replace existing when creating a module - :pull:`516`


0.33.3
------

Contains a small number of bug fixes and improvements. The most signicifact change is
the addition of a warning stating that `IDOM_FEATURE_INDEX_AS_DEFAULT_KEY=1` will become
the default in a future release. Beyond that, a lesser improvement makes it possible to
use the default export from a Javascript module when calling `module_from_template` by
specifying `exports_default=True` as a parameter. A

**Closed Issues**

- Memory leak in SharedClientStateServer - :issue:`511`
- Cannot use default export in react template - :issue:`502`
- Add warning that element index will be used as the default key in a future release - :issue:`428`

**Pull Requests**

- warn that IDOM_FEATURE_INDEX_AS_DEFAULT_KEY=1 will be the default - :pull:`515`
- clean up patch queues after exit - :pull:`514`
- Remove Reconnecting WS alert - :pull:`513`
- Fix 502 - :pull:`503`


0.33.2
------

A release to fix a memory leak caused by event handlers that were not being removed
when components updated.

**Closed Issues**

- Non-root component event handlers cause memory leaks - :issue:`510`


0.33.1
------

A hot fix for a regression introduced in ``0.33.0`` where the root element of the layout
could not be updated. See :issue:`498` for more info. A regression test for this will
be introduced in a future release.

**Pull Requests**

- Fix 498 pt1 - :pull:`501`


0.33.0
------

The most significant fix in this release is for a regression which manifested in
:issue:`480`, :issue:`489`, and :issue:`451` which resulted from an issue in the way
JSON patches were being applied client-side. This was ultimately resolved by
:pull:`490`. While it's difficult to test this without a more thorough Javascript
suite, we added a test that should hopefully catch this in the future by proxy.

The most important breaking change, is yet another which modifies the Custom Javascript
Component interface. We now add a ``create()`` function to the ``bind()`` interface that
allows IDOM's client to recursively create components from that (and only that) import
source. Prior to this, the interface was given unrendered models for child elements. The
imported module was then responsible for rendering them. This placed a large burden on
the author to understand how to handle these unrendered child models. In addition, in
the React template used by ``module_from_template`` we needed to import a version of
``idom-client-react`` from the CDN - this had already caused some issues where the
template required a version of ``idom-client-react`` in the which had not been released
yet.

**Closed Issues**

- Client-side error in mount-01d35dc3.js - :issue:`489`
- Style Cannot Be Updated - :issue:`480`
- Displaying error messages in the client via `__error__` tag can leak secrets - :issue:`454`
- Examples broken in docs  - :issue:`451`
- Rework docs landing page - :issue:`446`
- eventHandlers should be a mapping of generic callables - :issue:`423`
- Allow customization of built-in IDOM client - :issue:`253`

**Pull Requests**

- move VdomDict and VdomJson to proto - :pull:`492`
- only send error info in debug mode - :pull:`491`
- correcly apply client-side JSON patch - :pull:`490`
- add script to set version of all packages in IDOM - :pull:`483`
- Pass import source to bind - :pull:`482`
- Do not mutate client-side model - :pull:`481`
- assume import source children come from same source - :pull:`479`
- make an EventHandlerType protocol - :pull:`476`
- Update issue form - :pull:`471`


0.32.0
------

In addition to a variety of bug fixes and other minor improvements, there's a breaking
change to the custom component interface - instead of exporting multiple functions that
render custom components, we simply expect a single ``bind()`` function.
binding function then must return an object with a ``render()`` and ``unmount()``
function. This change was made in order to better support the rendering of child models.
See :ref:`Custom JavaScript Components` for details on the new interface.

**Closed Issues**

- Docs broken on Firefox - :issue:`469`
- URL resolution for web modules does not consider urls starting with / - :issue:`460`
- Query params in package name for module_from_template not stripped - :issue:`455`
- Make docs section margins larger - :issue:`450`
- Search broken in docs - :issue:`443`
- Move src/idom/client out of Python package - :issue:`429`
- Use composition instead of classes with Layout and LifeCycleHook  - :issue:`412`
- Remove Python language extension - :issue:`282`
- Add keys to models so React doesn't complain of child arrays requiring them -
  :issue:`255`
- Fix binder link in docs - :issue:`231`

**Pull Requests**

- Update issue form - :pull:`471`
- improve heading legibility - :pull:`470`
- fix search in docs by upgrading sphinx - :pull:`462`
- rework custom component interface with bind() func - :pull:`458`
- parse package as url path in module_from_template - :pull:`456`
- add file extensions to import - :pull:`439`
- fix key warnings - :pull:`438`
- fix #429 - move client JS to top of src/ dir - :pull:`430`


0.31.0
------

The :class:`~idom.core.layout.Layout` is now a prototype, and ``Layout.update`` is no
longer a public API. This is combined with a much more significant refactor of the
underlying rendering logic.

The biggest issue that has been resolved relates to the relationship between
:class:`~idom.core.hooks.LifeCycleHook` and ``Layout``. Previously, the
``LifeCycleHook`` accepted a layout instance in its constructor and called
``Layout.update``. Additionally, the ``Layout`` would manipulate the
``LifeCycleHook.component`` attribute whenever the component instance changed after a
render. The former behavior leads to a non-linear code path that's a touch to follow.
The latter behavior is the most egregious design issue since there's absolutely no local
indication that the component instance can be swapped out (not even a comment).

The new refactor no longer binds component or layout instances to a ``LifeCycleHook``.
Instead, the hook simply receives an unparametrized callback that can be triggered to
schedule a render. While some error logs lose clarity (since we can't say what component
caused them). This change precludes a need for the layout to ever mutate the hook.

To accomodate this change, the internal representation of the layout's state had to
change. Previsouly, a class-based approach was take, where methods of the state-holding
classes were meant to handle all use cases. Now we rely much more heavily on very simple
(and mostly static) data structures that have purpose built constructor functions that
much more narrowly address each use case.

After these refactors, ``ComponentTypes`` no longer needs a unique ``id`` attribute.
Instead, a unique ID is generated internally which is associated with the
``LifeCycleState``, not component instances since they are inherently transient.

**Pull Requests**

- fix #419 and #412 - :pull:`422`


0.30.1
------

Removes the usage of the :func:`id` function for generating unique ideas because there
were situations where the IDs bound to the lifetime of an object are problematic. Also
adds a warning :class:`Deprecation` warning to render functions that include the
parameter ``key``. It's been decided that allowing ``key`` to be used in this way can
lead to confusing bugs.

**Pull Requests**

- warn if key is param of component render function - :pull:`421`
- fix :issue:`417` and :issue:`413` - :pull:`418`
- add changelog entry for :ref:`0.30.0` - :pull:`415`


0.30.0
------

With recent changes to the custom component interface, it's now possible to remove all
runtime reliance on NPM. Doing so has many virtuous knock-on effects:

1. Removal of large chunks of code
2. Greatly simplifies how users dynamically experiment with React component libraries,
   because their usage no longer requires a build step. Instead they can be loaded in
   the browser from a CDN that distributes ESM modules.
3. The built-in client code needs to make fewer assumption about where static resources
   are located, and as a result, it's also easier to coordinate the server and client
   code.
4. Alternate client implementations benefit from this simplicity. Now, it's possible to
   install idom-client-react normally and write a ``loadImportSource()`` function that
   looks for route serving the contents of `IDOM_WEB_MODULES_DIR.`

This change includes large breaking changes:

- The CLI is being removed as it won't be needed any longer
- The `idom.client` is being removed in favor of a stripped down ``idom.web`` module
- The `IDOM_CLIENT_BUILD_DIR` config option will no longer exist and a new
  ``IDOM_WEB_MODULES_DIR`` which only contains dynamically linked web modules. While
  this new directory's location is configurable, it is meant to be transient and should
  not be re-used across sessions.

The new ``idom.web`` module takes a simpler approach to constructing import sources and
expands upon the logic for resolving imports by allowing exports from URLs to be
discovered too. Now, that IDOM isn't using NPM to dynamically install component
libraries ``idom.web`` instead creates JS modules from template files and links them
into ``IDOM_WEB_MODULES_DIR``. These templates ultimately direct the browser to load the
desired library from a CDN.

**Pull Requests**

- Add changelog entry for 0.30.0 - :pull:`415`
- Fix typo in index.rst - :pull:`411`
- Add event handlers docs - :pull:`410`
- Misc doc improvements - :pull:`409`
- Port first IDOM article to docs - :pull:`408`
- Test build in CI - :pull:`404`
- Remove all runtime reliance on NPM - :pull:`398`


0.29.0
------

Contains breaking changes, the most significant of which are:

- Moves the runtime client build directory to a "user data" directory rather a directory
  where IDOM's code was installed. This has the advantage of not requiring write
  permissions to rebuild the client if IDOM was installed globally rather than in a
  virtual environment.
- The custom JS component interface has been reworked to expose an API similar to
  the ``createElement``, ``render``, ``unmountComponentAtNode`` functions from React.

**Issues Fixed:**

- :issue:`375`
- :issue:`394`
- :issue:`401`

**Highlighted Commits:**

- add try/except around event handling - :commit:`f2bf589`
- do not call find_builtin_server_type at import time - :commit:`e29745e`
- import default from react/reactDOM/fast-json-patch - :commit:`74c8a34`
- no named exports for react/reactDOM - :commit:`f13bf35`
- debug logs for runtime build dir create/update - :commit:`af94f4e`
- put runtime build in user data dir - :commit:`0af69d2`
- change shared to update_on_change - :commit:`6c09a86`
- rework js module interface + fix docs - :commit:`699cc66`
- correctly serialize File object - :commit:`a2398dc`


0.28.0
------

Includes a wide variety of improvements:

- support ``currentTime`` attr of audio/video elements
- support for the ``files`` attribute from the target of input elements
- model children are passed to the Javascript ``mount()`` function
- began to add tests to client-side javascript
- add a ``mountLayoutWithWebSocket`` function to ``idom-client-react``

and breaking changes, the most significant of which are:

- Refactor existing server implementations as functions adhering to a protocol. This
  greatly simplified much of the code responsible for setting up servers and avoids
  the use of inheritance.
- Switch to a monorepo-style structure for Javascript enabling a greater separation of
  concerns and common workspace scripts in ``package.json``.
- Use a ``loadImportSource()`` function instead of trying to infer the path to dynamic
  modules which was brittle and inflexible. Allowing the specific client implementation
  to discover where "import sources" are located means ``idom-client-react`` doesn't
  need to try and devise a solution that will work for all cases. The fallout from this
  change is the addition of `importSource.sourceType` which, for the moment can either
  be ``"NAME"`` or ``"URL"`` where the former indicates the client is expected to know
  where to find a module of that name, and the latter should (usually) be passed on to
  ``import()``


**Issues Fixed:**

- :issue:`324` (partially resolved)
- :issue:`375`

**Highlighted Commits:**

- xfail due to bug in Python - :commit:`fee49a7`
- add importSource sourceType field - :commit:`795bf94`
- refactor client to use loadImportSource param - :commit:`bb5e3f3`
- turn app into a package - :commit:`b282fc2`
- add debug logs - :commit:`4b4f9b7`
- add basic docs about JS test suite - :commit:`9ecfde5`
- only use nox for python tests - :commit:`5056b7b`
- test event serialization - :commit:`05fd86c`
- serialize files attribute of file input element - :commit:`f0d00b7`
- rename hasMount to exportsMount - :commit:`d55a28f`
- refactor flask - :commit:`94681b6`
- refactor tornado + misc fixes to sanic/fastapi - :commit:`16c9209`
- refactor fastapi using server protocol - :commit:`0cc03ba`
- recactor sanic server - :commit:`43d4b4f`
- use server protocol instead of inheritance - :commit:`abe0fde`
- support currentTime attr of audio/video elements - :commit:`975b54a`
- pass children as props to mount() - :commit:`9494bc0`


0.27.0
------

Introduces changes to the interface for custom Javascript components. This now allows
JS modules to export a ``mount(element, component, props)`` function which can be used
to bind new elements to the DOM instead of using the application's own React instance
and specifying React as a peer dependency. This avoids a wide variety of potential
issues with implementing custom components and opens up the possibility for a wider
variety of component implementations.

**Highlighted Commits:**

- modules with mount func should not have children - :commit:`94d006c`
- limit to flask<2.0 - :commit:`e7c11d0`
- federate modules with mount function - :commit:`bf63a62`


0.26.0
------

A collection of minor fixes and changes that, as a whole, add up to something requiring
a minor release. The most significant addition is a fix for situations where a
``Layout`` can raise an error when a component whose state has been delete is rendered.
This occurs when element has been unmounted, but a latent event tells the layout it
should be updated. For example, when a user clicks a button rapidly, and the resulting
update deletes the original button.

**Highlighted Commits:**

- only one attr dict in vdom constructor - :commit:`555086a`
- remove Option setter/getter with current property - :commit:`2627f79`
- add cli command to show options - :commit:`c9e6869`
- check component has model state before render - :commit:`6a50d56`
- rename daemon to run_in_thread + misc - :commit:`417b687`


0.25.0
------

Completely refactors layout dispatcher by switching from a class-based approach to one
that leverages pure functions. While the logic itself isn't any simpler, it was easier
to implement, and now hopefully understand, correctly. This conversion was motivated by
several bugs that had cropped up related to improper usage of ``anyio``.

**Issues Fixed:**

- :issue:`330`
- :issue:`298`

**Highlighted Commits:**

- improve docs + simplify multiview - :commit:`4129b60`
- require anyio>=3.0 - :commit:`24aed28`
- refactor dispatchers - :commit:`ce8e060`


0.24.0
------

This release contains an update that allows components and elements to have "identity".
That is, their state can be preserved across updates. Before this point, only the state
for the component at the root of an update was preserved. Now though, the state for any
component and element with a ``key`` that is unique amongst its siblings, will be
preserved so long as this is also true for parent elements/components within the scope
of the current update. Thus, only when the key of the element or component changes will
its state do the same.

In a future update, the default key for all elements and components will be its index
with respect to its siblings in the layout. The
:attr:`~idom.config.IDOM_FEATURE_INDEX_AS_DEFAULT_KEY` feature flag has been introduced
to allow users to enable this behavior early.

**Highlighted Commits:**

- add feature flag for default key behavior - :commit:`42ee01c`
- use unique object instead of index as default key - :commit:`5727ab4`
- make HookCatcher/StaticEventHandlers testing utils - :commit:`1abfd76`
- add element and component identity - :commit:`5548f02`
- minor doc updates - :commit:`e5511d9`
- add tests for callback identity preservation with keys - :commit:`72e03ec`
- add 'key' to VDOM spec - :commit:`c3236fe`
- Rename validate_serialized_vdom to validate_vdom_json - :commit:`d04faf9`
- EventHandler should not serialize itself - :commit:`f7a59f2`
- fix docs typos - :commit:`42b2e20`
- fixes: #331 - add roadmap to docs - :commit:`4226c12`


0.23.1
------

**Highlighted Commits:**

- fix non-deterministic return order in install() - :commit:`494d5c2`


0.23.0
------

**Highlighted Commits:**

- add changelog to docs - :commit:`9cbfe94`
- automatically reconnect to server - :commit:`3477e2b`
- allow no reconnect in client - :commit:`ef263c2`
- cleaner way to specify import sources - :commit:`ea19a07`
- add the idom-react-client back into the main repo - :commit:`5dcc3bb`
- implement fastapi render server - :commit:`94e0620`
- improve docstring for IDOM_CLIENT_BUILD_DIR - :commit:`962d885`
- cli improvements - :commit:`788fd86`
- rename SERIALIZED_VDOM_JSON_SCHEMA to VDOM_JSON_SCHEMA - :commit:`74ad578`
- better logging for modules - :commit:`39565b9`
- move client utils into private module - :commit:`f825e96`
- redirect BUILD_DIR imports to IDOM_CLIENT_BUILD_DIR option - :commit:`53fb23b`
- upgrade snowpack - :commit:`5697a2d`
- better logs for idom.run + flask server - :commit:`2b34e3d`
- move package to src dir - :commit:`066c9c5`
- idom restore uses backup - :commit:`773f78e`
