---
title: Responding to Events 🚧
---

## Overview

<p class="intro" markdown>

React lets you add _event handlers_ to your PSX. Event handlers are your own functions that will be triggered in response to interactions like clicking, hovering, focusing form inputs, and so on.

</p>

!!! summary "You Will Learn"

    -   Different ways to write an event handler
    -   How to pass event handling logic from a parent component
    -   How events propagate and how to stop them

## Adding event handlers

To add an event handler, you will first define a function and then [pass it as a prop](../learn/passing-props-to-a-component.md) to the appropriate PSX tag. For example, here is a button that doesn't do anything yet:

=== "app.py"

    ```python
    {% include "../../examples/python/responding_to_events/simple_button.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

You can make it show a message when a user clicks by following these three steps:

1. Declare a function called `handle_click` _inside_ your `#!python def button():` component.
2. Implement the logic inside that function (use `print` to show the message).
3. Add `on_click=handle_click` to the `html.button` PSX.

=== "app.py"

    ```python
    {% include "../../examples/python/responding_to_events/simple_button_event.py" end="# end" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/css/responding_to_events/simple_button_event.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

You defined the `handle_click` function and then [passed it as a prop](../learn/passing-props-to-a-component) to `<button>`. `handle_click` is an **event handler.** Event handler functions:

-   Are usually defined _inside_ your components.
-   Have names that start with `handle`, followed by the name of the event.

By convention, it is common to name event handlers as `handle` followed by the event name. You'll often see `on_click=handle_click`, `on_mouse_enter=handle_mouse_enter`, and so on.

Alternatively, you can define an event handler inline in the PSX:

```python
html.button({"on_click": lambda event: print('You clicked me!')})
```

All of these styles are equivalent. Inline event handlers are convenient for short functions.

<Pitfall>

Functions passed to event handlers must be passed, not called. For example:

| passing a function (correct)      | calling a function (incorrect)      |
| --------------------------------- | ----------------------------------- |
| `html.button("on_click": handle_click)` | `html.button("on_click": handle_click())` |

The difference is subtle. In the first example, the `handle_click` function is passed as an `on_click` event handler. This tells React to remember it and only call your function when the user clicks the button.

In the second example, the `()` at the end of `handle_click()` fires the function _immediately_ during [rendering](../learn/render-and-commit), without any clicks. This is because Python inside the [PSX](../learn/javascript-in-jsx-with-curly-braces) executes right away.

When you write code inline, the same pitfall presents itself in a different way:

| passing a function (correct) | calling a function (incorrect) |
| --- | --- |
| `html.button("on_click": lambda event => print('...'))` | `html.button("on_click":  print('...'))` |

Passing inline code like this won't fire on click—it fires every time the component renders:

```python
// This alert fires when the component renders, not when clicked!
html.button({"on_click": lambda event: print('You clicked on me!')})
```

If you want to define your event handler inline, wrap it in an anonymous function like so:

```python
html.button({"on_click": lambda event: print('You clicked me!')})
```

Rather than executing the code inside with every render, this creates a function to be called later.

In both cases, what you want to pass is a function:

```python
	html.button({"on_click": handle_click}) # passes the `handle_click` function
	html.button({"on_click": lambda event: print('...')}) # passes the `lambda event: print('...')` function
```


</Pitfall>

### Reading props in event handlers

Because event handlers are declared inside of a component, they have access to the component's props. Here is a button that, when clicked, shows an alert with its `message` prop:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/reading_props_in_event_handlers.py" start="# start" %}
	```
=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/reading_props_in_event_handlers.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

This lets these two buttons show different messages. Try changing the messages passed to them.

### Passing event handlers as props

Often you'll want the parent component to specify a child's event handler. Consider buttons: depending on where you're using a `button` component, you might want to execute a different function—perhaps one plays a movie and another uploads an image.

To do this, pass a prop the component receives from its parent as the event handler like so:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/passing_event_handlers_as_props.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/passing_event_handlers_as_props.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

Here, the `toolbar` component renders a `play_button` and an `upload_button`:

-   `play_button` passes `handle_play_click` as the `on_click` prop to the `button` inside.
-   `upload_button` passes `lambda event: print('Uploading!')` as the `on_click` prop to the `button` inside.

Finally, your `button` component accepts a prop called `on_click`. It passes that prop directly to the built-in browser `<button>` with `on_click=on_click`. This tells React to call the passed function on click.

If you use a [design system](https://uxdesign.cc/everything-you-need-to-know-about-design-systems-54b109851969), it's common for components like buttons to contain styling but not specify behavior. Instead, components like `play_button` and `upload_button` will pass event handlers down.

### Naming event handler props

Built-in components like `<button>` and `<div>` only support [browser event names](../reference/react-dom/components/common#common-props) like `on_click`. However, when you're building your own components, you can name their event handler props any way that you like.

By convention, event handler props should start with `on`, followed by an underscore.

For example, the `button` component's `on_click` prop could have been called `on_smash`:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/naming_event_handler_props.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/naming_event_handler_props.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

In this example, `html.button("on_click"=on_smash)` shows that the browser `<button>` (lowercase) still needs a prop called `on_click`, but the prop name received by your custom `button` component is up to you!

When your component supports multiple interactions, you might name event handler props for app-specific concepts. For example, this `toolbar` component receives `on_play_movie` and `on_upload_image` event handlers:

=== "app.py"
	```python

	{% include "../../examples/python/responding_to_events/naming_event_handler_props_2.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/naming_event_handler_props.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

Notice how the `app` component does not need to know _what_ `toolbar` will do with `on_play_movie` or `on_upload_image`. That's an implementation detail of the `toolbar`. Here, `toolbar` passes them down as `on_click` handlers to its `button`s, but it could later also trigger them on a keyboard shortcut. Naming props after app-specific interactions like `on_play_movie` gives you the flexibility to change how they're used later.

<Note>

Make sure that you use the appropriate HTML tags for your event handlers. For example, to handle clicks, use [`html.button("on_click"=handleClick)`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button) instead of `html.div("on_click": handleClick)`. Using a real browser `<button>` enables built-in browser behaviors like keyboard navigation. If you don't like the default browser styling of a button and want to make it look more like a link or a different UI element, you can achieve it with CSS. [Learn more about writing accessible markup.](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML)

</Note>

## Event propagation

Event handlers will also catch events from any children your component might have. We say that an event "bubbles" or "propagates" up the tree: it starts with where the event happened, and then goes up the tree.

This `<div>` contains two buttons. Both the `<div>` _and_ each button have their own `on_click` handlers. Which handlers do you think will fire when you click a button?

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/event_propagation.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/event_propagation.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

If you click on either button, its `on_click` will run first, followed by the parent `<div>`'s `on_click`. So two messages will appear. If you click the toolbar itself, only the parent `<div>`'s `on_click` will run.

<Pitfall>

All events propagate in React except `on_scroll`, which only works on the PSX tag you attach it to.

</Pitfall>

### Stopping propagation

Event handlers receive an **event object** as their only argument. By convention, it's usually called `e`, which stands for "event". You can use this object to read information about the event.

That event object also lets you stop the propagation. If you want to prevent an event from reaching parent components, you need to call `e.stopPropagation()` like this `Button` component does:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/stopping_propagation.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/stopping_propagation.css" %}
	
	```

=== ":material-play: Run"
	```python
	# TODO
	```

When you click on a button:

1. React calls the `on_click` handler passed to `<button>`.
2. That handler, defined in `button`, does the following:
    - Calls `e.stop_propagation()`, preventing the event from bubbling further.
    - Calls the `on_click` function, which is a prop passed from the `toolbar` component.
3. That function, defined in the `toolbar` component, displays the button's own alert.
4. Since the propagation was stopped, the parent `<div>`'s `on_click` handler does _not_ run.

As a result of `e.stop_propagation()`, clicking on the buttons now only shows a single alert (from the `<button>`) rather than the two of them (from the `<button>` and the parent toolbar `<div>`). Clicking a button is not the same thing as clicking the surrounding toolbar, so stopping the propagation makes sense for this UI.

<DeepDive>

#### Capture phase events

In rare cases, you might need to catch all events on child elements, _even if they stopped propagation_. For example, maybe you want to log every click to analytics, regardless of the propagation logic. You can do this by adding `capture` at the end of the event name:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/capture_phase_events.py" start="# start" %}
	```


=== ":material-play: Run"
	```python
	# TODO
	```

Each event propagates in three phases:

1. It travels down, calling all `on_click_capture` handlers.
2. It runs the clicked element's `on_click` handler.
3. It travels upwards, calling all `on_click` handlers.

Capture events are useful for code like routers or analytics, but you probably won't use them in app code.

</DeepDive>

### Passing handlers as alternative to propagation

Notice how this click handler runs a line of code _and then_ calls the `on_click` prop passed by the parent:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/passing_handlers_as_alternative_to_propagation.py" start="# start" %}
	```


=== ":material-play: Run"
	```python
	# TODO
	```

You could add more code to this handler before calling the parent `on_click` event handler, too. This pattern provides an _alternative_ to propagation. It lets the child component handle the event, while also letting the parent component specify some additional behavior. Unlike propagation, it's not automatic. But the benefit of this pattern is that you can clearly follow the whole chain of code that executes as a result of some event.

If you rely on propagation and it's difficult to trace which handlers execute and why, try this approach instead.

### Preventing default behavior

Some browser events have default behavior associated with them. For example, a `<form>` submit event, which happens when a button inside of it is clicked, will reload the whole page by default:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/preventing_default_behavior.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/preventing_default_behavior.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

You can call `e.prevent_default()` on the event object to stop this from happening:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/preventing_default_behavior_2.py" start="# start" %}
	```

=== "styles.css"
	```css
	{% include "../../examples/css/responding_to_events/preventing_default_behavior_2.css" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

Don't confuse `event.stop_propagation()` and `event.prevent_default()`. They are both useful, but are unrelated:

-   [`e.stopPropagation()`](https://developer.mozilla.org/docs/Web/API/Event/stopPropagation) stops the event handlers attached to the tags above from firing.
-   [`e.preventDefault()` ](https://developer.mozilla.org/docs/Web/API/Event/preventDefault) prevents the default browser behavior for the few events that have it.

## Can event handlers have side effects?

Absolutely! Event handlers are the best place for side effects.

Unlike rendering functions, event handlers don't need to be [pure](../learn/keeping-components-pure), so it's a great place to _change_ something—for example, change an input's value in response to typing, or change a list in response to a button press. However, in order to change some information, you first need some way to store it. In React, this is done by using [state, a component's memory.](../learn/state-a-components-memory) You will learn all about it on the next page.

<Recap>

-   You can handle events by passing a function as a prop to an element like `<button>`.
-   Event handlers must be passed, **not called!** `on_click=handleClick`, not `on_click=handleClick()`.
-   You can define an event handler function separately or inline.
-   Event handlers are defined inside a component, so they can access props.
-   You can declare an event handler in a parent and pass it as a prop to a child.
-   You can define your own event handler props with application-specific names.
-   Events propagate upwards. Call `event.stop_sropagation()` on the first argument to prevent that.
-   Events may have unwanted default browser behavior. Call `event.prevent_default()` to prevent that.
-   Explicitly calling an event handler prop from a child handler is a good alternative to propagation.

</Recap>

<Challenges>

#### Fix an event handler

Clicking this button is supposed to switch the page background between white and black. However, nothing happens when you click it. Fix the problem. (Don't worry about the logic inside `handle_click`—that part is fine.)

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/fix_an_event_handler_problem.py" start="# start" %}
	```

=== ":material-play: Run"
	```python
	# TODO
	```

<Solution>

The problem is that `html.button("on_click": handle_click())` _calls_ the `handle_click` function while rendering instead of _passing_ it. Removing the `()` call so that it's `html.button("on_click": handleClick)` fixes the issue:

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/fix_an_event_handler_solution.py" start="# start" %}
	```

=== ":material-play: Run"
	```python
	# TODO	
	```

Alternatively, you could wrap the call into another function, like `html.button({"on_click": lambda event: handle_click()})`

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/fix_an_event_handler_solution_2.py" start="# start" %}
	```

=== ":material-play: Run"
	```python
	# TODO	
	```
</Solution>

#### Wire up the events

This `color_switch` component renders a button. It's supposed to change the page color. Wire it up to the `on_change_color` event handler prop it receives from the parent so that clicking the button changes the color.

After you do this, notice that clicking the button also increments the page click counter. Your colleague who wrote the parent component insists that `on_change_color` does not increment any counters. What else might be happening? Fix it so that clicking the button _only_ changes the color, and does _not_ increment the counter.

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/wire_up_the_events_problem.py" start="# start" %}
	```

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/wire_up_the_events_problem_2.py" start="# start" %}
	```

=== ":material-play: Run"
	```python
	# TODO	
	```

<Solution>

First, you need to add the event handler, like `html.button("on_click": on_change_color)`.

However, this introduces the problem of the incrementing counter. If `on_change_color` does not do this, as your colleague insists, then the problem is that this event propagates up, and some handler above does it. To solve this problem, you need to stop the propagation. But don't forget that you should still call `on_change_color`.

=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/wire_up_the_events_solution.py" start="# start" %}
	```


=== "app.py"
	```python
	{% include "../../examples/python/responding_to_events/wire_up_the_events_solution_2.py" start="# start" %}
	```

=== ":material-play: Run"
	```python
	# TODO	
	```

</Solution>

</Challenges>
