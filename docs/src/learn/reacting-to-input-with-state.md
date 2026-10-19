## Overview

<p class="intro" markdown>

ReactPy provides a declarative way to manipulate the UI. Instead of manipulating individual pieces of the UI directly, you describe the different states your component can be in, and switch between them in response to the user input. This is similar to how designers think about the UI.

</p>

!!! summary "You will learn"

    -   How declarative UI programming differs from imperative UI programming
    -   How to enumerate the different visual states your component can be in
    -   How to trigger the changes between the different visual states from code

## How declarative UI compares to imperative

When you design UI interactions, you probably think about how the UI _changes_ in response to user actions. Consider a form that lets the user submit an answer:

-   When you type something into the form, the "Submit" button **becomes enabled.**
-   When you press "Submit", both the form and the button **become disabled,** and a spinner **appears.**
-   If the request succeeds, the form **gets hidden,** and a "Thank you" message **appears.**
-   If the request fails, an error message **appears,** and the form **becomes enabled** again.

In **imperative programming,** the above corresponds directly to how you implement interaction. You have to write the exact instructions to manipulate the UI depending on what just happened. Here's another way to think about this: imagine riding next to someone in a car and telling them turn by turn where to go. They don't know where you want to go, they just follow your commands. (And if you get the directions wrong, you end up in the wrong place!) It's called _imperative_ because you have to "command" each element, from the spinner to the button, telling the computer _how_ to update the UI:

```js linenums="0"
async function handleFormSubmit(e) {
    e.preventDefault();
    disable(textarea);
    disable(button);
    show(loadingMessage);
    hide(errorMessage);
    try {
        await submitForm(textarea.value);
        show(successMessage);
        hide(form);
    } catch (err) {
        show(errorMessage);
        errorMessage.textContent = err.message;
    } finally {
        hide(loadingMessage);
        enable(textarea);
        enable(button);
    }
}

function handleTextareaChange() {
    if (textarea.value.length === 0) {
        disable(button);
    } else {
        enable(button);
    }
}

function hide(el) {
    el.style.display = "none";
}

function show(el) {
    el.style.display = "";
}

function enable(el) {
    el.disabled = false;
}

function disable(el) {
    el.disabled = true;
}
```

Manipulating the UI imperatively works well enough for isolated examples, but it gets exponentially more difficult to manage in more complex systems. Adding a new UI element or a new interaction would require carefully checking all existing code to make sure you haven't introduced a bug (for example, forgetting to show or hide something).

ReactPy was built to solve this problem.

In ReactPy, you don't directly manipulate the UI — meaning you don't enable, disable, show, or hide components directly. Instead, you **declare what you want to show,** and ReactPy figures out how to update the UI.

This is less a stylistic preference than a physical constraint: a ReactPy server component has no DOM to manipulate. Your code runs on the server and returns a description of the UI; there is no `#!python element` object to set `#!python .style.display` on. See [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) for the one narrow escape hatch and why it rarely helps.

## Thinking about UI declaratively

You've learned that CSS enables declarative string-based styling so you can describe _what_ to show, not _how_ to show it. You can also learn to think about your ReactPy components declaratively.

ReactPy stands at the intersection of design and computer science, so both of these ideas are sources of inspiration. To think declaratively, take each possible state of a component's UI, break it down into a list, and then write code to describe each state at once.

### Step 1: Identify your component's different visual states

First, enumerate the visual states of the UI the user could see:

1. **Empty** — the form has no answer yet.
2. **Typing** — the form has a non-empty answer.
3. **Submitting** — the answer has just been submitted and nothing else can be clicked.
4. **Success** — the user wants to see a "Correct!" message instead of the form.
5. **Error** — like Typing, but with an error message.

Replace the `#!python form()` component with a mock that returns the right UI based on a `#!python status` prop:

=== "app.py"

    ```python
    {% include "../../examples/reacting_to_input_with_state/status_mock/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/reacting_to_input_with_state/status_mock/styles.css" %}
    ```

=== ":material-play: Run"

The `#!python status` prop is a "mock" of the state inside the component, and controls which visual states the user will see. This mock is controlled by a prop called `#!python status` with a default value of `#!python "empty"`.

You could call that prop anything you like, the naming is not important. Try changing the default to `#!python status="success"` to see the success message appear. **Mocking lets you quickly iterate on the UI before you wire up any logic.**

Two details in that mock are worth pointing out. "Typing" and "Submitting" render the same layout, differing only in whether the controls are disabled — so the difference is expressed as data, not as a different branch of markup:

```python linenums="0"
html.button({"disabled": status in {"empty", "submitting"}}, "Submit")
```

And the error state deliberately keeps the form enabled. A state that showed an error while also disabling the input would leave the user unable to correct their answer — imperative code has to enforce that by hand, and it is exactly the kind of thing that gets forgotten.

!!! info "Displaying many visual states at once"

    You could try each state by editing the source, but then you'd navigate back and forth many times. It's often easier to show many visual states at once, like a "living styleguide" or "storybook":

    === "app.py"

        ```python
        {% include "../../examples/reacting_to_input_with_state/styleguide/app.py" start="# start" %}
        ```

    === "styles.css"

        ```css
        {% include "../../examples/reacting_to_input_with_state/styleguide/styles.css" %}
        ```

    === ":material-play: Run"

    Because the mock is driven by a prop, all five states mount side by side and can be compared without a single click. Each `#!python html.section()` carries a `#!python "key"` because they are children of a list.

### Step 2: Determine what triggers those state changes

There are two categories of "cause" that can change state in a component:

-   **Input** (the user typing, clicking, changing a field, and so on)
-   **Output** (one of the component's effects completing — a timer firing, a request finishing, and so on)

In both cases, **you must set [state variables](./state-a-components-memory.md#anatomy-of-use_state) to update the UI.**

-   **Changing the text input** (human) should switch it from the _Empty_ state to the _Typing_ state or back, depending on whether the text box is empty or not.
-   **Clicking the Submit button** (human) should switch it to the _Submitting_ state.
-   **A successful response** (computer) should switch it to the _Success_ state.
-   **A failed response** (computer) should switch it to the _Error_ state with the matching error message.

!!! note ""

    Notice that human inputs often require [event handlers!](./responding-to-events.md)

### Step 3: Represent the state in memory with `#!python use_state`

Next you'll need to represent the visual states of your component in memory with [`#!python use_state.`](../reference/use-state.md)

Simplicity is key: each piece of state is a "moving piece", and **you want as few "moving pieces" as possible.** More complexity leads to more bugs!

Start with the state that everyone agrees on:

```python linenums="0"
answer, set_answer = use_state("")
error, set_error = use_state("")
```

Then you'll need a state variable representing which of the visual states to display. There's usually more than a single way to represent that in memory, so you'll need to experiment with it. Here's one attempt — a boolean per state:

```python linenums="0"
is_empty, set_is_empty = use_state(True)
is_typing, set_is_typing = use_state(False)
is_submitting, set_is_submitting = use_state(False)
is_success, set_is_success = use_state(False)
is_error, set_is_error = use_state(False)
```

### Step 4: Remove any non-essential state variables

You want to avoid duplication in the state content so you're only tracking what is essential. Spending a little time refactoring your state structure will make your components easier to understand, reduce duplication, and avoid unintended meanings. **Your goal is to prevent the cases where the state in memory doesn't represent any valid UI that you'd want a user to see.**

Take those five booleans:

-   `#!python is_typing` and `#!python is_submitting` can't both be `#!python True`. A paradox usually means the state is not constrained enough. There are four possible combinations of two booleans, but only three correspond to valid states. To remove the "impossible" state, combine them into a `#!python status` that must be one of three values: `#!python "typing"`, `#!python "submitting"`, or `#!python "success"`.
-   Another paradox: `#!python is_empty` and `#!python is_typing` can't both be `#!python True`. Keeping them as separate state variables risks them going out of sync and causing bugs. Fortunately you can drop `#!python is_empty` and check `#!python len(answer) == 0` instead.
-   `#!python is_error` is not needed, because you can check `#!python if error` instead.

After this clean-up you're left with 3 (down from 7!) _essential_ state variables:

```python linenums="0"
answer, set_answer = use_state("")
error, set_error = use_state("")
status, set_status = use_state("typing")  # 'typing', 'submitting', or 'success'
```

You know they are essential, because you can't remove any of them without breaking the functionality.

!!! info "Eliminating 'impossible' states with a reducer"

    These three variables are a good enough representation of this form's state. However, some intermediate states still don't fully make sense. A non-empty `#!python error` doesn't make sense when `#!python status` is `#!python "success"`. [Reducers](./extracting-state-logic-into-a-reducer.md) let you unify multiple state variables into a single object and consolidate all the related logic!

### Step 5: Connect the event handlers to set state

Finally, connect the event handlers to the `#!python set` functions from Step 4:

=== "app.py"

    ```python
    {% include "../../examples/reacting_to_input_with_state/final_form/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/reacting_to_input_with_state/final_form/styles.css" %}
    ```

=== ":material-play: Run"

Three things are worth noticing.

**The handlers only set state.** You never say "hide the textarea" or "enable the button". The `#!python disabled` attributes and the error paragraph are computed from `#!python status` and `#!python error` on every render, so it's impossible to end up in a state where one was updated and the other wasn't. Submitting a wrong answer really does lock the form, then bring back the form with the error message and the input usable again.

**The error is stored as a string, not an exception.** React's version keeps an `#!python Error` object and reads `#!python .message` off it. In Python, store the message — `#!python str(exc)` — and render it directly.

**`#!python event.preventDefault()` matters here, and ReactPy reads your code to find it.** Without it the browser navigates away and your app is gone. Detection happens by inspecting the handler's code rather than at call time, so an `#!python async def` handler that calls `#!python event.preventDefault()` before its `#!python await` is still detected. What defeats it is indirection: rebinding the argument (`#!python e = event`) or delegating to a helper hides the call from the handler's own code, and the default is *not* prevented. If you can't put the call in the handler itself, declare it with [`#!python @event(prevent_default=True)`](./responding-to-events.md).

!!! warning "An `#!python await` in the handler means an extra paint"

    Calling `#!python set_status("submitting")` *before* `#!python await submit_form(answer)` is what makes the locked-form state visible at all: ReactPy renders what has been set so far when the handler suspends, so you see the form lock, then the result arrive. That is the behaviour you want here.

    It is narrower than React's batching, and will surprise you when you _don't_ want the intermediate paint. See [Queueing a Series of State Updates](./queueing-a-series-of-state-updates.md) for the measured difference.

Although this code is longer than the original imperative example, it is much less fragile. Expressing all interactions as state changes lets you introduce new visual states later without breaking existing ones. It also lets you change what should be displayed in each state without changing the logic of the interaction itself.

## Recap

-   Declarative programming means describing the UI for each visual state rather than micromanaging the UI (imperative).
-   Identify the visual states, and mock them with a prop so all of them can be seen at once.
-   Then:
    -   Determine the possible causes — user inputs and computer outputs.
    -   Represent those states with as few state variables as possible, and remove any that can be derived.
    -   Connect the event handlers to set state.
