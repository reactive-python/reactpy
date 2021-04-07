Roadmap
=======

2021-Q2
-------

**Element and Component Identity**:
    At the moment, whenever a particular branch of a layout is updated, all the state
    (i.e. hooks and event handlers) that live within that branch are thrown away and
    reconstructed. Given IDOM's current implementation for
    :class:`~idom.core.layout.Layout` this is unavoidable. To resolve this issue, we
    need to add a concept of `"keys" <https://reactjs.org/docs/lists-and-keys.html>`__
    which can be used to indicate the identity of an element within the layout
    structure. For example, if you have a list of elements that get re-ordered when a
    button is pressed, their state should be preserved, and reassigned to their new
    location in the layout.

    By default React requires keys to be used to communicate element identity whenever
    the order or number of simbling elements can change. While there are clear
    performance benefits for adhering to this stipulation, it's often confusing for new
    developers. React has the further advantage of the JSX syntax, which makes it easier
    for the program to determine exactly when keys must be supplied by the user. To make
    the experience for new users simpler, and due to a lack of inforcement via JSX, IDOM
    will be to assume that any element without a key is new. Thus, for IDOM, keys will
    primarilly be a tool for optimization rather than a functional requirement.

    Related issues:

    - https://github.com/idom-team/idom/issues/330
    - https://github.com/idom-team/idom/issues/19

**Reconsider Custom Component Interface**:
    One problem that's come up several times while implementing alternate client
    solutions with React is that custom components must use the same React instances
    as the client. This is problematic for developers of these custom components because
    they need purpose-built
    `compiler plugins <https://github.com/idom-team/idom-react-component-cookiecutter/blob/1cc31b8690f84cb90dd861f2f47873b1d5711f74/%7B%7Bcookiecutter.repository_name%7D%7D/js/rollup.config.js>`__
    that will convert imports of React to point to the location ``react.js`` will be
    once the component has been loaded via :class:`~idom.client.module.Module`.

    Ideally developers of custom components should be able to operate in isolation
    without assuming anything about the environment they are running in. This has the
    benefit of simplifying the development workflow as well as making it possible to
    incorperate components from other Javascript frameworks (e.g. Vue) without much
    effort.

    Related issues:

    - https://github.com/idom-team/idom-jupyter/issues/13
    - https://github.com/idom-team/idom-dash/issues/6
