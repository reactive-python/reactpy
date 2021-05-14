Changelog
=========

0.27.0
------

Introduces changes to the interface for custom Javascript components. This now allows
JS modules to export a ``mount(element, component, props)`` function which can be used
to bind new elements to the DOM instead of using the application's own React instance
and specifying React as a peer dependency. This avoids a wide variety of potential
issues with implementing custom components and opens up the possiblity for a wider
variety of component implementations.

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

- only one attr dict in vdom constructor - :commit:`555086a`
- remove Option setter/getter with current property - :commit:`2627f79`
- add cli command to show options - :commit:`c9e6869`
- check component has model state before render - :commit:`6a50d56`
- rename daemon to run_in_thread + misc - :commit:`417b687`

0.25.0
------

Completely refactors :ref:`Layout Dispatchers <Layout Dispatcher>` by switching from a
class-based approach to one that leverages pure functions. While the logic itself isn't
any simpler, it was easier to implement, and now hopefully understand, correctly. This
conversion was motivated by several bugs that had cropped up related to improper usage
of ``anyio``.

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
- Rename validate_serialized_vdom to validate_vdom - :commit:`d04faf9`
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
