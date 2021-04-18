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

- add feature flag for default key behavior - `42ee01c <https://github.com/idom-team/idom/commit/42ee01c>`__
- use unique object instead of index as default key - `5727ab4 <https://github.com/idom-team/idom/commit/5727ab4>`__
- make HookCatcher/StaticEventHandlers testing utils - `1abfd76 <https://github.com/idom-team/idom/commit/1abfd76>`__
- add element and component identity - `5548f02 <https://github.com/idom-team/idom/commit/5548f02>`__
- minor doc updates - `e5511d9 <https://github.com/idom-team/idom/commit/e5511d9>`__
- add tests for callback identity preservation with keys - `72e03ec <https://github.com/idom-team/idom/commit/72e03ec>`__
- add 'key' to VDOM spec - `c3236fe <https://github.com/idom-team/idom/commit/c3236fe>`__
- Rename validate_serialized_vdom to validate_vdom - `d04faf9 <https://github.com/idom-team/idom/commit/d04faf9>`__
- EventHandler should not serialize itself - `f7a59f2 <https://github.com/idom-team/idom/commit/f7a59f2>`__
- fix docs typos - `42b2e20 <https://github.com/idom-team/idom/commit/42b2e20>`__
- fixes: #331 - add roadmap to docs - `4226c12 <https://github.com/idom-team/idom/commit/4226c12>`__

0.23.1
------

- fix non-deterministic return order in install() - `494d5c2 <https://github.com/idom-team/idom/commit/494d5c2>`__

0.23.0
------

- add changelog to docs - `9cbfe94 <https://github.com/idom-team/idom/commit/9cbfe94>`__
- automatically reconnect to server - `3477e2b <https://github.com/idom-team/idom/commit/3477e2b>`__
- allow no reconnect in client - `ef263c2 <https://github.com/idom-team/idom/commit/ef263c2>`__
- cleaner way to specify import sources - `ea19a07 <https://github.com/idom-team/idom/commit/ea19a07>`__
- add the idom-react-client back into the main repo - `5dcc3bb <https://github.com/idom-team/idom/commit/5dcc3bb>`__
- implement fastapi render server - `94e0620 <https://github.com/idom-team/idom/commit/94e0620>`__
- improve docstring for IDOM_CLIENT_BUILD_DIR - `962d885 <https://github.com/idom-team/idom/commit/962d885>`__
- cli improvements - `788fd86 <https://github.com/idom-team/idom/commit/788fd86>`__
- rename SERIALIZED_VDOM_JSON_SCHEMA to VDOM_JSON_SCHEMA - `74ad578 <https://github.com/idom-team/idom/commit/74ad578>`__
- better logging for modules - `39565b9 <https://github.com/idom-team/idom/commit/39565b9>`__
- move client utils into private module - `f825e96 <https://github.com/idom-team/idom/commit/f825e96>`__
- redirect BUILD_DIR imports to IDOM_CLIENT_BUILD_DIR option - `53fb23b <https://github.com/idom-team/idom/commit/53fb23b>`__
- upgrade snowpack - `5697a2d <https://github.com/idom-team/idom/commit/5697a2d>`__
- better logs for idom.run + flask server - `2b34e3d <https://github.com/idom-team/idom/commit/2b34e3d>`__
- move package to src dir - `066c9c5 <https://github.com/idom-team/idom/commit/066c9c5>`__
- idom restore uses backup - `773f78e <https://github.com/idom-team/idom/commit/773f78e>`__
