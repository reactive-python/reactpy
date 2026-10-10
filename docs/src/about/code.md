## Overview

<p class="intro" markdown>

ReactPy takes pull requests from anyone, and most of what gets rejected is not wrong — it is unreviewable. A short branch, a focused diff, and the checks run before you open the pull request is what makes a change easy to say yes to. This page covers the mechanics: where the code lives, how to branch, and what CI will run against you.

</p>

!!! summary "You will learn"

    -   Which branch a change belongs on, and why that matters here more than elsewhere
    -   The commit and pull request conventions this repository enforces
    -   What CI checks, before CI tells you

## Know which repository you are in

This documentation site and the library are separate bodies of work, and the commands that work in one do nothing in the other.

| Change | Repository / branch |
| --- | --- |
| Library code, hooks, layout, backends | [`reactive-python/reactpy` → `main`](https://github.com/reactive-python/reactpy) |
| JavaScript client (`src/js/`) | Same, `main` |
| These documentation pages (`docs/src/`, `docs/examples/`) | [`reactive-python/reactpy` → `new-docs`](https://github.com/reactive-python/reactpy/tree/new-docs) |

The `new-docs` branch holds only `docs/` — the package and `tests/` were removed from it. A test command run there reports success without running anything.

!!! warning "Pitfall"

    Confirm the branch before you start typing, not after. A library fix committed onto the docs branch looks fine locally and becomes a rebase chore later. `git branch --show-current` costs nothing and settles it.

## Before you start

Look for an open discussion or issue that matches what you intend to do. If one exists, comment there before writing code — a maintainer who has already thought about the problem will usually redirect you in one sentence, and that sentence is cheaper than a rejected pull request. If none exists, open a [discussion](https://github.com/reactive-python/reactpy/discussions) first.

For anything larger than a bug fix, expect the answer to be "show me the design first". A draft pull request is the right medium for that: it runs CI, it is reviewable, and it says plainly that it is not ready to merge.

## Branch, commit, push

Fork the repository if you do not have write access, then branch from an up-to-date `main`:

```bash
git checkout -b fix-my-change main
```

Name the branch for the change, not for you. `fix-key-not-resetting-on-provider` beats `patch-1` and survives a month of review.

Match the convention of the branch you are landing on; they differ. Documentation commits on `new-docs` use [Conventional Commits](https://www.conventionalcommits.org/) subjects — `docs(learn): author X for ReactPy v2`, `docs(examples): fix include-marker cropping`. Library history on `main` instead uses plain sentence subjects, because pull requests there are squash-merged and the summary is written at merge time — `Fix PyScript root component not hiding after render error (#1347)`. In both cases the subject is the thing a reader scans to find the functional change in a long history, so write it for that reader.

One commit per logical change. If a commit only makes sense next to a later one, squash them before you push rather than asking the reviewer to mentally reassemble them.

## The checklist

The repository ships a pull request template; fill it in rather than deleting it.

-   [ ] Tests have been developed for bug fixes or new functionality.
-   [ ] The changelog has been updated, if necessary.
-   [ ] Documentation has been updated, if necessary.
-   [ ] GitHub Issues closed by this pull request have been linked.

By submitting, you agree that your contribution complies with the project's open source licenses.

Tests are not optional for a behaviour change. A bug fix should arrive with the test that reproduces the bug — write it first and watch it fail, then fix and watch it pass. A test that has never failed proves nothing about the thing it claims to protect.

The changelog rule is narrower than it looks: `CHANGELOG.md` gets an entry under `Unreleased` for **user-facing** changes only. Test-only, docs-only, and CI-only changes get none. Adding one for those is a small annoyance to the person doing the release, who then has to notice and delete it. See [Changelog](./changelog.md).

## What CI runs

Understanding the gate is cheaper than discovering it in a failed run.

```
hatch test --parallel --cover --retries 10          # coverage job
hatch test --parallel --retries 10                  # ubuntu, macos, windows × 3.11–3.14
hatch fmt src/reactpy --check                       # lint + format
hatch run python:type_check                         # pyright
hatch run javascript:test
hatch run javascript:check
```

Run the equivalents locally before you push — the same commands, not approximations of them:

```bash
hatch fmt --check
hatch run python:type_check
hatch test -k the_test_you_touched
```

CI retries flaky tests, which is a mercy and a trap: a genuinely racy test can go green on the third attempt and stay in the tree. If a test fails once and passes on retry, that is a bug in the test — usually a bare `asyncio.sleep` where `poll(...)` belongs.

Documentation pull requests run a different gate — the `mkdocs build --strict` set described in [Running Tests](./running-tests.md).

## Working with reviewers

Respond to every comment, including the ones you are not acting on. "Not taking this because X" is a complete reply and saves a round trip; silence invites a re-review of something you already considered.

Push fixes as new commits rather than force-pushing over the reviewed range. Reviewers read the delta between your last push and this one; a force-push that rewrites history they already read makes them re-read the whole diff, and they will notice when they skip it.

If a review asks for something you believe is wrong, say so once, with evidence, and then defer if the maintainer still wants it. Review is a conversation with an asymmetry: they own the file after you leave.

!!! abstract "Note"

    When a review is posted by an automated tool, the maintainers still own the decision. Do not treat "the bot did not complain" as approval, and do not treat a bot comment as a demand — respond on the merits, the same as any other comment.

## After merge

Documentation changes on `new-docs` deploy to the live site on push, so a mistake there is visible immediately rather than at the next release. That is a reason to run the build check locally, not a reason to be nervous about contributing.

Library changes reach users only through a release, which the maintainers cut. Do not ask when your fix will ship, and do not close a closed-issue loop by demanding a release — the tag is a maintainer's call.

## Recap

-   Library work on `main`; documentation work on `new-docs`. Check the branch first.
-   Start from a discussion; a one-sentence redirect beats a rejected pull request.
-   Conventional Commit subjects, one logical change per commit, branch named for the change.
-   Tests accompany behaviour changes, and they must have failed first.
-   Changelog entries for user-facing changes only.
-   Run CI's exact commands locally before pushing; treat a flaky test as a bug.

## Related

-   [Running Tests](./running-tests.md) — the commands, and how to read their failures
-   [Contributing Documentation](./docs.md) — page conventions and the examples workflow
-   [Changelog](./changelog.md) — format, categories, and what counts as user-facing
-   [Community](./community.md) — where to raise the issue before you write the fix
