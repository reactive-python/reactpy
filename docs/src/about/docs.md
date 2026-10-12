## Overview

<p class="intro" markdown>

Most of these pages were ported from the ReactJS documentation, and the port is the whole job: a page is done when every claim in it is true of ReactPy and every snippet in it runs. That is a lower bound on effort and an upper bound on trustworthiness, which is the trade this project made deliberately. This page is how to do the work and how to know it is finished.

</p>

!!! summary "You will learn"

    -   What makes a ported page "done", and how the `🚧` marker works
    -   The page structure, admonitions, and link conventions this site uses
    -   Why snippets live in `docs/examples/` instead of inside the markdown

## Where things live

```
docs/
├── mkdocs.yml          # nav: — every page must be listed here
├── src/                # the pages, in markdown
│   ├── learn/          #   tutorials and concepts
│   ├── reference/      #   API reference
│   └── about/          #   this section
├── examples/           # runnable Python, one directory per page slug
└── overrides/          # template overrides
```

Page files are `kebab-case.md`; example directories are the same name with underscores (`learn/scaling-up-with-reducer-and-context.md` → `examples/scaling_up_with_reducer_and_context/`). A new page must be added to `nav:` in `mkdocs.yml`, but the build will not tell you when you forget: a page missing from `nav:` is still built and served, and `mkdocs build --strict` exits **0**. The only trace is an `INFO` line listing the unlisted pages. Read it: every page currently on that list carries a `Planned / Undeveloped` banner in its body and can be ignored, which is exactly how a page you did mean to publish would hide among them. Adding the entry is what puts the page in the site's navigation, which is the actual reason to do it.

## What "done" means

A page is authored, not migrated. Concretely:

-   Every code sample is ReactPy that runs. No JSX, no `className=` outside an attribute dict, no hook that does not exist.
-   Every behavioural claim has been checked against the package or its tests — by reading the source, and for anything about rendering or events, by running it.
-   React-only sections are removed or rewritten, not translated.
-   The `🚧` badge is gone from its `nav:` entry.

!!! abstract "Note"

    `🚧` in the navigation means "this is still a ReactJS page with the React names swapped". It is a promise to the reader that the content is unreliable, so removing it is the meaningful act — the badge should never come off before the checks above are true. `🚫` means the page is blocked on something outside this project and is parked; commented-out `nav:` entries work the same way.

## Port, do not rename

The pages derive from [react.dev](https://react.dev/learn). Editing means deleting what is false as much as replacing what is named differently, and the failure mode is a page that reads fluently and is wrong.

Things that do not survive a rename:

-   **Hooks that do not exist.** ReactPy has twelve hooks. There is no `use_id`, `use_transition`, `use_deferred_value`, `use_layout_effect`, `use_insertion_effect`, `use_imperative_handle`, or `use_sync_external_store`. Some of the react.dev pages for them are parked as `🚫`; `use_id` has no page at all, because the upstream issue was closed as not planned. Never port a page that depends on one as if it worked.
-   **Naming rules.** Components are snake_case and lowercase — `my_button`, not `MyButton`. React's capital-letter rule does not apply, because ReactPy distinguishes a component from a tag by the call, not the case. Attribute keys stay camelCase (`className`, `onClick`), because those pass through to the DOM untouched.
-   **JSX mechanics.** Children are positional arguments after an optional attribute dict. There is no JSX, and no PSX in this release.
-   **StrictMode and `memo`.** Neither exists. React's double-invoke warnings and its "skip re-rendering unchanged children" optimisation have no ReactPy equivalent, so port those sections as a warning that ReactPy will not catch the problem for you.
-   **`&&` rendering.** `{cond && <X/>}` has no safe Python spelling — `False and X` leaks the word `False` into the page, since only `None` renders nothing. Rewrite such examples rather than transliterating them.
-   **Dependency arrays.** `use_effect`, `use_memo`, and `use_callback` infer dependencies from the closure when you omit the argument. React's "omit the array to run after every render" is simply wrong here.

!!! warning "Pitfall"

    A page can pass every automated check while teaching something false, because the checks are syntactic. The ReactJS FIXME that sat in `thinking-in-react.md` claiming `event["target"]["checked"]` does not work was wrong — a checkbox `onChange` receives `checked=True`. The only defence is running the example and reading what the client actually sent.

## Page structure

Every authored page opens the same way: an `## Overview` heading, an intro paragraph in a `<p class="intro">` block, then a `You will learn` summary.

```markdown
## Overview

<p class="intro" markdown>

One or two paragraphs that say what the page solves and why it matters in ReactPy specifically.

</p>

!!! summary "You will learn"

    -   Bullet
    -   Bullet
```

Then the body as `##` and `###` sections, closing with `## Recap` (bulleted, factual) and `## Related` (links with a dash and a phrase explaining each).

Admonitions come from the Material theme plus `assets/css/admonition.css`. The set in use:

| Admonition | For |
| --- | --- |
| `!!! summary "You will learn"` | Objectives, once, after the intro |
| `!!! abstract "Note"` | Clarification that is not a warning |
| `!!! warning "Pitfall"` | A mistake the reader is likely to make |
| `!!! info "Deep Dive"` | Deeper mechanics a reader can skip |
| `!!! example "Terminal"` | A shell session |

ReactJS's `<Pitfall>`, `<DeepDive>`, `<Recap>`, `<Challenges>`, `<Solution>`, and `<Hint>` JSX tags have no MkDocs equivalent. Convert them to admonitions or headings; never copy them through, since an unrecognised tag renders as literal text.

Links are relative `.md` paths from the current file — `../reference/use-state.md`, `./extracting-state-logic-into-a-reducer.md#the-rule-reactpy-adds` — not site-absolute paths like `/learn/...`, which break under versioned builds and make `--strict` unable to verify them.

Code fences: ` ```python linenums="0" ` for fragments, bare ` ```python ` for full-file tabs, and `hl_lines="3-4 7"` to mark the lines under discussion. Inline code that is Python gets the `#!python` prefix (`\`#!python use_state\``) so it highlights.

## Examples are the source of truth

Snippets are not typed into the markdown. They are real files under `docs/examples/<page_slug>/`, pulled in by the include plugin:

```markdown
=== "app.py"

    ```python
    {% include "../../examples/quick_start/my_button.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```
```

The rules that make this work:

-   The file is a complete, importable module — black-formatted at 88 columns, imports at the top.
-   A `# start` marker on its own line is what the include begins after; `# end` stops it. Crop at the marker so the marker itself never renders on the page.
-   A file with no marker is included whole.
-   Multiple variants of one idea go in sibling directories (`task_state_props/`, `task_context/`, `task_wiring/`), one tabbed group per example.
-   The `:material-play: Run` tab is a standing placeholder. Keep it.

Because the file is included, a snippet cannot drift from a runnable example — but nothing in the build proves the example *behaves*. Mount it and check the DOM before you write "this renders a list". When a page compares several versions, drive all of them through the same click sequence and assert the same observable output; "it looks the same" is how two versions of an example quietly disagree.

Also list children of a component with `key=` when they come from a list — `html.ul([row(item, key=item["id"]) for item in items])`. Omitting it renders fine and emits a debug-mode warning, which is exactly the lesson the page about keys is trying to teach.

## Verifying a page

From the repository root:

```bash
hatch fmt --check docs/
pyright --pythonpath <your-env>/bin/python docs/
cd docs && mkdocs build --strict; echo "exit=$?"
```

Then run the examples themselves and open the built page in a browser. `mkdocs build --strict` catches broken internal links and unresolvable includes — both abort the build with a nonzero exit. Two things it does **not** catch: a page missing from `nav:` (an `INFO` line, exit 0), and a link whose `#anchor` does not exist in an otherwise valid target file (also exit 0), so check both by eye. And it cannot catch a snippet that renders nothing.

You are the only gate. The single workflow on `new-docs` runs `mkdocs gh-deploy --force` on push, and `gh-deploy` does not pass `--strict` — a build with broken links exits 0 and publishes. A miss does not fail a pipeline; it goes live.

!!! warning "Pitfall"

    Do not trust a component that renders without error. Set `REACTPY_DEBUG=1` when probing: with debug off, a component that raised produces `{"tagName": "", "error": ""}` — a blank region and a 200 response. See [Running Tests](./running-tests.md) for the harness traps that make a broken example look green.

## Process

Branch from `new-docs`, one page per branch, and use the same Conventional Commit subjects as the history there — `docs(learn): author X for ReactPy v2`. A commit that removes a `🚧` badge from `nav:` should be the same commit that authored the page, never a separate "mark done" commit that could be cherry-picked alone.

No `CHANGELOG.md` entry: documentation work is not user-facing in the sense the changelog means. See [Changelog](./changelog.md).

!!! abstract "Note"

    `docs/src/dictionary.txt` exists for the spellcheck plugin, which is currently commented out in `mkdocs.yml`. New domain words belong there if the plugin is ever re-enabled; nothing fails while it stays off.

## Recap

-   A page is done when it runs and every claim is verified — then remove its `🚧` badge.
-   Port, do not rename: delete JSX, non-existent hooks, StrictMode, `memo`, `&&` rendering, and React's dependency-array semantics.
-   Fixed structure: Overview, intro paragraph, `You will learn`, sections, Recap, Related.
-   Relative `.md` links; admonitions instead of ReactJS's JSX tags.
-   Snippets are includes from `docs/examples/`, cropped at `# start`, formatted at 88 columns.
-   `--strict` checks links and nothing about behaviour. Run the example.

## Related

-   [Running Tests](./running-tests.md) — the exact commands and how to read their failures
-   [Contributing Code](./code.md) — branch and pull request conventions
-   [Changelog](./changelog.md) — what does and does not deserve an entry
-   [Community](./community.md) — where to ask about a page before rewriting it
