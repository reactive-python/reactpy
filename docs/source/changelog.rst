Changelog
=========

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

- fix non-deterministic return order in install() - :commit:`494d5c2`

0.23.0
------

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
