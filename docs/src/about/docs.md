## Overview

<p class="intro" markdown>

Most of these pages were ported from the ReactJS documentation, and the port is the whole job: a page is done when every claim in it is true of ReactPy and every snippet in it runs. That is a lower bound on effort and an upper bound on trustworthiness, which is the trade this project made deliberately. This page is how to do the work and how to know it is finished.

</p>

!!! summary "You will learn"

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


## Port, do not rename

The pages derive from [react.dev](https://react.dev/learn). Editing means deleting what is false as much as replacing what is named differently, and the failure mode is a page that reads fluently and is wrong.

Things that do not survive a rename:

-   **Hooks that do not exist.** ReactPy has twelve hooks. There is no `use_id`, `use_transition`, `use_deferred_value`, `use_layout_effect`, `use_insertion_effect`, `use_imperative_handle`, or `use_sync_external_store`.
-   **Naming rules.** Components are snake_case and lowercase — `my_button`, not `MyButton`. React's capital-letter rule does not apply, because ReactPy distinguishes a component from a tag by the call, not the case. Attribute keys stay camelCase (`className`, `onClick`), because those pass through to the DOM untouched.
-   **JSX mechanics.** Children are positional arguments after an optional attribute dict. There is no JSX, and no PSX in this release.
-   **StrictMode and `memo`.** Neither exists. React's double-invoke warnings and its "skip re-rendering unchanged children" optimisation have no ReactPy equivalent, so port those sections as a warning that ReactPy will not catch the problem for you.
-   **`&&` rendering.** `{cond && <X/>}` has no safe Python spelling — `False and X` leaks the word `False` into the page, since only `None` renders nothing. Rewrite such examples rather than transliterating them.
-   **Dependency arrays.** `use_effect`, `use_memo`, and `use_callback` infer dependencies from the closure when you omit the argument. React's "omit the array to run after every render" is slightly different from ReactPy's behaviour.

!!! warning "Pitfall"

    A page can pass every automated check while teaching something false, because the checks are syntactic. The ReactJS FIXME that sat in `thinking-in-react.md` claiming `checked` was not delivered was wrong — a checkbox `onChange` handler reads it back as `#!python await event.target.checked`. The only defence is running the example against a real layout and reading what the client actually answered.

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
```

The rules that make this work:

-   The file is a complete, importable module — black-formatted at 88 columns, imports at the top.
-   A `# start` marker on its own line is what the include begins after; `# end` stops it. Crop at the marker so the marker itself never renders on the page.
-   A file with no marker is included whole.
-   Multiple variants of one idea go in sibling directories (`task_state_props/`, `task_context/`, `task_wiring/`), one tabbed group per example.
-   The `:material-play: Run` tab is left **empty**, and `docs/plugins/reactpy_run.py` fills it in. It reads the demo off the include directives in the tab set's sibling tabs, so the tab runs exactly the code the reader can already see — in the browser, through the same PyScript runtime ReactPy ships. Opening the tab is what executes the demo, so there is no Run button and nothing to type; while Pyodide boots, the panel reads `Loading...`. Keep the tab.

Because the file is included, a snippet cannot drift from a runnable example — but nothing in the build proves the example *behaves*. Mount it and check the DOM before you write "this renders a list". When a page compares several versions, drive all of them through the same click sequence and assert the same observable output; "it looks the same" is how two versions of an example quietly disagree.

### When Run has to be told

Inference covers a tab set that shows one demo's files. It gives up, and says why inside the tab, when the sibling tabs name two example directories, or when the component to mount takes required props. Give the tab a `reactpy-run` fence as its body to answer:

```markdown
=== ":material-play: Run"

    ```reactpy-run
    dir: rules_of_react/impure_render
    files: app.py
    root: counter
    props: symbol="BTC"
    ```
```

-   `dir:` — which example directory, when the sibling tabs name two.
-   `files:` — which files make up the demo, relative to that directory.
-   `root:` — which component to mount, when the outermost one is not the one nothing else renders.
-   `props:` — arguments for a component whose parameters have no defaults.

A demo that needs a filesystem, a server, or threads cannot run under Pyodide at all. Delete its Run tab instead of leaving a tab that opens onto nothing — `docs/examples/manually_register_a_client/badge_module/` is the precedent.

Also list children of a component with `key=` when they come from a list — `html.ul([row(item, key=item["id"]) for item in items])`. Omitting it renders fine and emits a debug-mode warning, which is exactly the lesson the page about keys is trying to teach.

### print() has somewhere to go

An example that prints gets a console region under its own output — Python's equivalent of React's browser console, and the reason the effect-timing lessons (`print("connected")`, `print(f"subscribe {topic}")`) show anything at all.

It belongs to the example rather than the page. One PyScript interpreter runs every demo on a page, so `sys.stdout` is shared and redirecting it would mix the demos together with no way to sort them back out; the runner shadows `print` inside the example instead. That is also what makes a print inside an event handler or an effect land correctly — a `redirect_stdout` wrapped around the example's first execution would be gone by the time those run. Only `print()` is routed, so `sys.stdout` writes are not.

### Images belong to the docs

Demo images live in `docs/src/assets/images/demos/`. Every page that shows one sits two levels below the site root — `/learn/rendering-lists/`, `/about/docs/` — so write the path from there, right where the `<img>` needs it:

```python
html.img({"src": "../../assets/images/demos/yXOvdOSs.jpg", "alt": "Hedy Lamarr"})
```

Relative rather than absolute, because `hatch run docs:serve` and the deployed site are different origins: an absolute URL to `reactive-python.github.io` makes a locally served page fetch images that were never deployed, so a brand-new image looks broken on your machine and fine in review — the reverse of how bugs usually behave. The two `../` are load-bearing. Move a demo to a page one level deeper or shallower and the same string resolves somewhere else, breaking the image only on that page; `docs/plugins/reactpy_run.py` fails the build when that happens, so fix the base when you move the demo.

Do not hotlink someone else's image host. These files were `i.imgur.com` links copied from the React docs, and imgur answers `403` to a request that carries a `Referer` — so every `<img>` in a demo was a broken placeholder while the very same URL opened in a new tab loaded fine. That asymmetry is why it survived: a plain `curl` passes, and so does an automated check that only asserts the demo rendered. React has since vendored the identical files to its own CDN under the same names, which is where these copies came from.

## Verifying a page

From the repository root:

```bash
hatch fmt --check docs/
pyright --pythonpath <your-env>/bin/python docs/
cd docs && mkdocs build --strict; echo "exit=$?"
```

Then run the examples themselves and open the built page in a browser. `mkdocs build --strict` catches broken internal links and unresolvable includes — both abort the build with a nonzero exit. Two things it does **not** catch: a page missing from `nav:` (an `INFO` line, exit 0), and a link whose `#anchor` does not exist in an otherwise valid target file (also exit 0), so check both by eye. And it cannot catch a snippet that renders nothing.

!!! warning "Pitfall"

    Do not trust a component that renders without error. Set `REACTPY_DEBUG=1` when probing: with debug off, a component that raised produces `{"tagName": "", "error": ""}` — a blank region and a 200 response. See [Running Tests](./running-tests.md) for the harness traps that make a broken example look green.

## Recap

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
