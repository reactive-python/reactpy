## Overview

<p class="intro" markdown>

ReactPy's source is MIT-licensed. Much of the prose you are reading is derived from the ReactJS documentation, which carries a separate Creative Commons licence, and the two do not cover the same things. This page states which licence applies to what, and what you owe when you reuse either.

</p>

!!! summary "You will learn"

    -   Which licence covers the code, and which covers these pages
    -   Why the distinction matters when you copy from one side
    -   Where the third-party components in a ReactPy install come from

## Source code

The ReactPy package is released under the MIT licence, copyright Reactive Python and affiliates. The full text lives in the license file at the [repository root](https://github.com/reactive-python/reactpy/tree/main) and is reproduced below.

MIT is permissive: use, copy, modify, merge, publish, distribute, sublicense, and sell, subject to keeping the copyright notice and licence text in copies of the software. It comes with no warranty, and liability is excluded.

```text
{% include "../../../LICENSE.md" %}
```

## Documentation

These pages are a different body of work from the code, and they are separately encumbered.

Much of this documentation — including its layout and much of its content — was created with heavy influence from [react.dev](https://react.dev/), which is licensed under the [Creative Commons Attribution 4.0 International](https://raw.githubusercontent.com/reactjs/reactjs.org/b2d5613b6ae20855ced7c83067b604034bebbb44/LICENSE-DOCS.md) licence. ReactPy's behaviour often mirrors React's closely enough that the documents paraphrase, and in places copy, React's language and examples.

!!! abstract "Note"

    CC BY 4.0 is also permissive, but its condition is *attribution* rather than keeping a licence block. If you copy substantial prose from these pages into your own documentation, credit ReactPy and, where the text is close to React's original, acknowledge the ReactJS documentation as the further source. Attributing to ReactPy alone is not sufficient for the passages that came from React.

The practical boundary: code you write against ReactPy is yours, unencumbered by either licence. These pages are text under a credit-bearing licence. A snippet in `docs/examples/` is code that happens to be inside a document — treat it as MIT, since its purpose is to be pasted into a project.

## Third-party components

A working ReactPy install bundles more than this repository's source: the browser-side client, the vendored JavaScript dependencies, and, for client-side rendering, PyScript. Each keeps its own upstream licence, shipped with the distribution.

Check what a release actually contains rather than trusting a summary — the package metadata and the `static/` directory of the release are authoritative, and the licence files travel inside the wheel.

## Licensing your own contribution

The pull request template ends with an agreement that contributions comply with the project's open source licences. It is a checkbox, but it is the whole of the provenance control this project has, so it is worth taking literally:

-   Do not paste code you do not have the right to redistribute. Code copied from a licence-incompatible project, or from an answer on a forum, is the common failure.
-   Do not copy substantial prose from react.dev into these pages without acknowledging the source on the page or in the commit.
-   If you adapted something, say what and from where in the pull request description. It costs you a sentence and saves the maintainer an investigation.

## Recap

-   Source code: MIT, in `LICENSE.md` at the repository root.
-   These pages: derived from the ReactJS docs under CC BY 4.0 — attribution is the obligation.
-   Snippets in `docs/examples/` exist to be pasted; treat them as MIT code.
-   Bundled JavaScript and PyScript keep their upstream licences, shipped with the release.
-   Contributions must be yours to license; say what you adapted and from where.

## Related

-   [Contributing Documentation](./docs.md) — how pages here are authored, and where React-derived text comes from
-   [Contributing Code](./code.md) — the pull request checklist, including the licence agreement
-   [Community](./community.md) — how to reach a maintainer about a licensing question
-   [Changelog](./changelog.md) — the release history
