## Overview

<p class="intro" markdown>

ReactPy is built in the open. Questions, bug reports, and ideas all have a home, and the same places are where you get help when an example on this site stops behaving. This page is a map of those places and what belongs in each.

</p>

!!! summary "You will learn"

    -   Where to ask a question, report a bug, and propose a feature
    -   Which channels are official, and which are just links people repeat
    -   What the code of conduct expects, and what to include in a report

## Where everything happens

The [ReactPy repository on GitHub](https://github.com/reactive-python/reactpy) is the centre of gravity. Everything else points back to it.

| You want to | Go to |
| --- | --- |
| Ask how to do something | [Discussions → Question](https://github.com/reactive-python/reactpy/discussions/categories/question) |
| Report something broken | [Discussions → Problem](https://github.com/reactive-python/reactpy/discussions/categories/problem) |
| Propose a feature | [Discussions → Ideas](https://github.com/reactive-python/reactpy/discussions/categories/ideas) |
| Show off what you built | [Discussions → Share](https://github.com/reactive-python/reactpy/discussions/categories/share) |
| Publish a package you made | [Discussions → Downloadable Packages](https://github.com/reactive-python/reactpy/discussions/categories/downloadable-packages) |
| Track a confirmed defect | [Issues](https://github.com/reactive-python/reactpy/issues) |
| Chat in real time | [Discord](https://discord.gg/uNb5P4hA9X) |

Discussions is the front door, not Issues. The repository's issue-template configuration disables blank issues and points new visitors at Discussions instead, so a question opened as an issue gets redirected rather than answered. Open an issue once a defect is confirmed and someone has reproduced it — the discussion that came first usually becomes the link inside it.

## Chat

There is a [Discord server](https://discord.gg/uNb5P4hA9X) for ReactPy, announced in [Discussion #997](https://github.com/reactive-python/reactpy/discussions/997) and linked from the repository README. It is the fastest place to get an answer to a "why is this doing that" question, and quiet enough that nobody minds a beginner question.

!!! abstract "Note"

    An invite URL is mutable third-party state. If `discord.gg/uNb5P4hA9X` ever stops resolving, read the current invite from the README badge or from Discussion #997 — those two are maintained together — rather than trusting a search result, which may point at a cloned server.

Discord is good for conversation and bad for searchability. A solution that exists only in chat is invisible to the next person with the same problem. If a chat thread solves something real, post it to Discussions afterwards; if it exposes an error on this site, that is a [documentation contribution](./docs.md).

## Code of conduct

Participation is governed by the [Contributor Covenant code of conduct](https://github.com/reactive-python/reactpy/blob/main/CODE_OF_CONDUCT.md), which lives at the repository root. It applies everywhere the project is discussed — Discussions, Issues, pull requests, Discord, and any other space where ReactPy maintainers show up.

The practical version: assume good faith, criticise code rather than people, and accept that "this is obvious" is rarely true of the person asking. The enforcement section of the document names the contact route for escalating a problem.

## Packages outside this repository

ReactPy's core deliberately stays small, so much of what you might expect to find here lives in sibling repositories. Each has its own issue tracker — do not file a Django problem against the core repo.

-   [reactpy-router](https://github.com/reactive-python/reactpy-router) — URL routing
-   [reactpy-django](https://github.com/reactive-python/reactpy-django) — Django integration
-   [reactpy-jupyter](https://github.com/reactive-python/reactpy-jupyter) — Jupyter integration
-   [reactpy-js-component-template](https://github.com/reactive-python/reactpy-js-component-template) — starting point for a custom JavaScript component

Community-built packages are announced in [Discussions → Downloadable Packages](https://github.com/reactive-python/reactpy/discussions/categories/downloadable-packages). Those are third-party: they are not reviewed before being posted, they are not pinned against a ReactPy release, and an unanswered thread there says nothing about the library. See [Tools, Libraries, and Packages](../learn/tools-and-packages.md) for how to evaluate one.

## Supporting the project

ReactPy is maintained by volunteers on their own time. [GitHub Sponsors](https://github.com/sponsors/archmonger) is the route the project uses, matching the maintainers listed in the repository's funding configuration.

Sponsoring buys maintenance, not priority. It does not queue your issue and does not entitle anyone to a feature. If you need a specific behaviour on a deadline, the reliable path is to write it — or fund someone to write it — and open a pull request.

## What to include when you ask

Most unanswered questions are unanswered because they cannot be reproduced. Four things turn a vague report into one someone can act on:

-   The exact ReactPy version. Run `pip show reactpy` and paste it. Behaviour shifts between pre-releases, so `2.0.0b13` and `2.0.0` are different answers.
-   The Python version and operating system.
-   The smallest snippet that still misbehaves. Cutting an app down to one component usually finds the bug before you post it.
-   Both sides of the comparison: what happened, and what you expected. For a rendering problem, include what the browser showed, not only what the code says.

!!! warning "Pitfall"

    "It doesn't work" with no traceback is not a question anyone can answer, and the error you think is irrelevant often is not the relevant one. Include the full traceback *and* the server-side console output. ReactPy logs failing event handlers and effects on the **server** while the browser stays silent, so a UI that merely stops responding usually has a server line that explains it — see [Creating VDOM Event Handlers](../learn/creating-vdom-event-handlers.md).

## Recap

-   Ask in [Discussions](https://github.com/reactive-python/reactpy/discussions); open an issue only for a confirmed defect.
-   Real-time chat is on [Discord](https://discord.gg/uNb5P4hA9X); follow up anything durable in Discussions so it stays searchable.
-   The [code of conduct](https://github.com/reactive-python/reactpy/blob/main/CODE_OF_CONDUCT.md) governs every one of those spaces.
-   Integration packages live in sibling repos; file bugs against the repo that owns the behaviour.
-   Reproducible reports get answers: versions, smallest failing snippet, and the server log.

## Related

-   [Contributing Code](./code.md) — turning a bug you found into a merged fix
-   [Contributing Documentation](./docs.md) — fixing a page that misled you
-   [Running Tests](./running-tests.md) — the commands to run before opening a pull request
-   [Tools, Libraries, and Packages](../learn/tools-and-packages.md) — choosing between built-in and third-party
