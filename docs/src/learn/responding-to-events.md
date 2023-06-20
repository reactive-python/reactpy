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

You defined the `handleClick` function and then [passed it as a prop](/learn/passing-props-to-a-component) to `<button>`. `handleClick` is an **event handler.** Event handler functions:

-   Are usually defined _inside_ your components.
-   Have names that start with `handle`, followed by the name of the event.

By convention, it is common to name event handlers as `handle` followed by the event name. You'll often see `on_click={handleClick}`, `onMouseEnter={handleMouseEnter}`, and so on.

Alternatively, you can define an event handler inline in the JSX:

```jsx
<button on_click={function handleClick() {
  alert('You clicked me!');
}}>
```

Or, more concisely, using an arrow function:

```jsx
<button on_click={() => {
  alert('You clicked me!');
}}>
```

All of these styles are equivalent. Inline event handlers are convenient for short functions.

<Pitfall>

Functions passed to event handlers must be passed, not called. For example:

| passing a function (correct)      | calling a function (incorrect)      |
| --------------------------------- | ----------------------------------- |
| `<button on_click={handleClick}>` | `<button on_click={handleClick()}>` |

The difference is subtle. In the first example, the `handleClick` function is passed as an `on_click` event handler. This tells React to remember it and only call your function when the user clicks the button.

In the second example, the `()` at the end of `handleClick()` fires the function _immediately_ during [rendering](/learn/render-and-commit), without any clicks. This is because JavaScript inside the [JSX `{` and `}`](/learn/javascript-in-jsx-with-curly-braces) executes right away.

When you write code inline, the same pitfall presents itself in a different way:

| passing a function (correct) | calling a function (incorrect) |
| --- | --- |
| `<button on_click={() => alert('...')}>` | `<button on_click={alert('...')}>` |

Passing inline code like this won't fire on click—it fires every time the component renders:

```jsx
// This alert fires when the component renders, not when clicked!
<button on_click={alert('You clicked me!')}>
```

If you want to define your event handler inline, wrap it in an anonymous function like so:

```jsx
<button on_click={() => alert('You clicked me!')}>
```

Rather than executing the code inside with every render, this creates a function to be called later.

In both cases, what you want to pass is a function:

-   `<button on_click={handleClick}>` passes the `handleClick` function.
-   `<button on_click={() => alert('...')}>` passes the `() => alert('...')` function.

[Read more about arrow functions.](https://javascript.info/arrow-functions-basics)

</Pitfall>

### Reading props in event handlers

Because event handlers are declared inside of a component, they have access to the component's props. Here is a button that, when clicked, shows an alert with its `message` prop:

```js
function AlertButton({ message, children }) {
	return <button on_click={() => alert(message)}>{children}</button>;
}

export default function Toolbar() {
	return (
		<div>
			<AlertButton message="Playing!">Play Movie</AlertButton>
			<AlertButton message="Uploading!">Upload Image</AlertButton>
		</div>
	);
}
```

```css
button {
	margin-right: 10px;
}
```

This lets these two buttons show different messages. Try changing the messages passed to them.

### Passing event handlers as props

Often you'll want the parent component to specify a child's event handler. Consider buttons: depending on where you're using a `Button` component, you might want to execute a different function—perhaps one plays a movie and another uploads an image.

To do this, pass a prop the component receives from its parent as the event handler like so:

```js
function Button({ on_click, children }) {
	return <button on_click={on_click}>{children}</button>;
}

function PlayButton({ movieName }) {
	function handlePlayClick() {
		alert(`Playing ${movieName}!`);
	}

	return <Button on_click={handlePlayClick}>Play "{movieName}"</Button>;
}

function UploadButton() {
	return <Button on_click={() => alert("Uploading!")}>Upload Image</Button>;
}

export default function Toolbar() {
	return (
		<div>
			<PlayButton movieName="Kiki's Delivery Service" />
			<UploadButton />
		</div>
	);
}
```

```css
button {
	margin-right: 10px;
}
```

Here, the `Toolbar` component renders a `PlayButton` and an `UploadButton`:

-   `PlayButton` passes `handlePlayClick` as the `on_click` prop to the `Button` inside.
-   `UploadButton` passes `() => alert('Uploading!')` as the `on_click` prop to the `Button` inside.

Finally, your `Button` component accepts a prop called `on_click`. It passes that prop directly to the built-in browser `<button>` with `on_click={on_click}`. This tells React to call the passed function on click.

If you use a [design system](https://uxdesign.cc/everything-you-need-to-know-about-design-systems-54b109851969), it's common for components like buttons to contain styling but not specify behavior. Instead, components like `PlayButton` and `UploadButton` will pass event handlers down.

### Naming event handler props

Built-in components like `<button>` and `<div>` only support [browser event names](/reference/react-dom/components/common#common-props) like `on_click`. However, when you're building your own components, you can name their event handler props any way that you like.

By convention, event handler props should start with `on`, followed by a capital letter.

For example, the `Button` component's `on_click` prop could have been called `onSmash`:

```js
function Button({ onSmash, children }) {
	return <button on_click={onSmash}>{children}</button>;
}

export default function App() {
	return (
		<div>
			<Button onSmash={() => alert("Playing!")}>Play Movie</Button>
			<Button onSmash={() => alert("Uploading!")}>Upload Image</Button>
		</div>
	);
}
```

```css
button {
	margin-right: 10px;
}
```

In this example, `<button on_click={onSmash}>` shows that the browser `<button>` (lowercase) still needs a prop called `on_click`, but the prop name received by your custom `Button` component is up to you!

When your component supports multiple interactions, you might name event handler props for app-specific concepts. For example, this `Toolbar` component receives `onPlayMovie` and `onUploadImage` event handlers:

```js
export default function App() {
	return (
		<Toolbar
			onPlayMovie={() => alert("Playing!")}
			onUploadImage={() => alert("Uploading!")}
		/>
	);
}

function Toolbar({ onPlayMovie, onUploadImage }) {
	return (
		<div>
			<Button on_click={onPlayMovie}>Play Movie</Button>
			<Button on_click={onUploadImage}>Upload Image</Button>
		</div>
	);
}

function Button({ on_click, children }) {
	return <button on_click={on_click}>{children}</button>;
}
```

```css
button {
	margin-right: 10px;
}
```

Notice how the `App` component does not need to know _what_ `Toolbar` will do with `onPlayMovie` or `onUploadImage`. That's an implementation detail of the `Toolbar`. Here, `Toolbar` passes them down as `on_click` handlers to its `Button`s, but it could later also trigger them on a keyboard shortcut. Naming props after app-specific interactions like `onPlayMovie` gives you the flexibility to change how they're used later.

<Note>

Make sure that you use the appropriate HTML tags for your event handlers. For example, to handle clicks, use [`<button on_click={handleClick}>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button) instead of `<div on_click={handleClick}>`. Using a real browser `<button>` enables built-in browser behaviors like keyboard navigation. If you don't like the default browser styling of a button and want to make it look more like a link or a different UI element, you can achieve it with CSS. [Learn more about writing accessible markup.](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML)

</Note>

## Event propagation

Event handlers will also catch events from any children your component might have. We say that an event "bubbles" or "propagates" up the tree: it starts with where the event happened, and then goes up the tree.

This `<div>` contains two buttons. Both the `<div>` _and_ each button have their own `on_click` handlers. Which handlers do you think will fire when you click a button?

```js
export default function Toolbar() {
	return (
		<div
			className="Toolbar"
			on_click={() => {
				alert("You clicked on the toolbar!");
			}}
		>
			<button on_click={() => alert("Playing!")}>Play Movie</button>
			<button on_click={() => alert("Uploading!")}>Upload Image</button>
		</div>
	);
}
```

```css
.Toolbar {
	background: #aaa;
	padding: 5px;
}
button {
	margin: 5px;
}
```

If you click on either button, its `on_click` will run first, followed by the parent `<div>`'s `on_click`. So two messages will appear. If you click the toolbar itself, only the parent `<div>`'s `on_click` will run.

<Pitfall>

All events propagate in React except `onScroll`, which only works on the JSX tag you attach it to.

</Pitfall>

### Stopping propagation

Event handlers receive an **event object** as their only argument. By convention, it's usually called `e`, which stands for "event". You can use this object to read information about the event.

That event object also lets you stop the propagation. If you want to prevent an event from reaching parent components, you need to call `e.stopPropagation()` like this `Button` component does:

```js
function Button({ on_click, children }) {
	return (
		<button
			on_click={(e) => {
				e.stopPropagation();
				on_click();
			}}
		>
			{children}
		</button>
	);
}

export default function Toolbar() {
	return (
		<div
			className="Toolbar"
			on_click={() => {
				alert("You clicked on the toolbar!");
			}}
		>
			<Button on_click={() => alert("Playing!")}>Play Movie</Button>
			<Button on_click={() => alert("Uploading!")}>Upload Image</Button>
		</div>
	);
}
```

```css
.Toolbar {
	background: #aaa;
	padding: 5px;
}
button {
	margin: 5px;
}
```

When you click on a button:

1. React calls the `on_click` handler passed to `<button>`.
2. That handler, defined in `Button`, does the following:
    - Calls `e.stopPropagation()`, preventing the event from bubbling further.
    - Calls the `on_click` function, which is a prop passed from the `Toolbar` component.
3. That function, defined in the `Toolbar` component, displays the button's own alert.
4. Since the propagation was stopped, the parent `<div>`'s `on_click` handler does _not_ run.

As a result of `e.stopPropagation()`, clicking on the buttons now only shows a single alert (from the `<button>`) rather than the two of them (from the `<button>` and the parent toolbar `<div>`). Clicking a button is not the same thing as clicking the surrounding toolbar, so stopping the propagation makes sense for this UI.

<DeepDive>

#### Capture phase events

In rare cases, you might need to catch all events on child elements, _even if they stopped propagation_. For example, maybe you want to log every click to analytics, regardless of the propagation logic. You can do this by adding `Capture` at the end of the event name:

```js
<div
	on_clickCapture={() => {
		/* this runs first */
	}}
>
	<button on_click={(e) => e.stopPropagation()} />
	<button on_click={(e) => e.stopPropagation()} />
</div>
```

Each event propagates in three phases:

1. It travels down, calling all `on_clickCapture` handlers.
2. It runs the clicked element's `on_click` handler.
3. It travels upwards, calling all `on_click` handlers.

Capture events are useful for code like routers or analytics, but you probably won't use them in app code.

</DeepDive>

### Passing handlers as alternative to propagation

Notice how this click handler runs a line of code _and then_ calls the `on_click` prop passed by the parent:

```js
function Button({ on_click, children }) {
	return (
		<button
			on_click={(e) => {
				e.stopPropagation();
				on_click();
			}}
		>
			{children}
		</button>
	);
}
```

You could add more code to this handler before calling the parent `on_click` event handler, too. This pattern provides an _alternative_ to propagation. It lets the child component handle the event, while also letting the parent component specify some additional behavior. Unlike propagation, it's not automatic. But the benefit of this pattern is that you can clearly follow the whole chain of code that executes as a result of some event.

If you rely on propagation and it's difficult to trace which handlers execute and why, try this approach instead.

### Preventing default behavior

Some browser events have default behavior associated with them. For example, a `<form>` submit event, which happens when a button inside of it is clicked, will reload the whole page by default:

```js
export default function Signup() {
	return (
		<form onSubmit={() => alert("Submitting!")}>
			<input />
			<button>Send</button>
		</form>
	);
}
```

```css
button {
	margin-left: 5px;
}
```

You can call `e.preventDefault()` on the event object to stop this from happening:

```js
export default function Signup() {
	return (
		<form
			onSubmit={(e) => {
				e.preventDefault();
				alert("Submitting!");
			}}
		>
			<input />
			<button>Send</button>
		</form>
	);
}
```

```css
button {
	margin-left: 5px;
}
```

Don't confuse `e.stopPropagation()` and `e.preventDefault()`. They are both useful, but are unrelated:

-   [`e.stopPropagation()`](https://developer.mozilla.org/docs/Web/API/Event/stopPropagation) stops the event handlers attached to the tags above from firing.
-   [`e.preventDefault()` ](https://developer.mozilla.org/docs/Web/API/Event/preventDefault) prevents the default browser behavior for the few events that have it.

## Can event handlers have side effects?

Absolutely! Event handlers are the best place for side effects.

Unlike rendering functions, event handlers don't need to be [pure](/learn/keeping-components-pure), so it's a great place to _change_ something—for example, change an input's value in response to typing, or change a list in response to a button press. However, in order to change some information, you first need some way to store it. In React, this is done by using [state, a component's memory.](/learn/state-a-components-memory) You will learn all about it on the next page.

<Recap>

-   You can handle events by passing a function as a prop to an element like `<button>`.
-   Event handlers must be passed, **not called!** `on_click={handleClick}`, not `on_click={handleClick()}`.
-   You can define an event handler function separately or inline.
-   Event handlers are defined inside a component, so they can access props.
-   You can declare an event handler in a parent and pass it as a prop to a child.
-   You can define your own event handler props with application-specific names.
-   Events propagate upwards. Call `e.stopPropagation()` on the first argument to prevent that.
-   Events may have unwanted default browser behavior. Call `e.preventDefault()` to prevent that.
-   Explicitly calling an event handler prop from a child handler is a good alternative to propagation.

</Recap>

<Challenges>

#### Fix an event handler

Clicking this button is supposed to switch the page background between white and black. However, nothing happens when you click it. Fix the problem. (Don't worry about the logic inside `handleClick`—that part is fine.)

```js
export default function LightSwitch() {
	function handleClick() {
		let bodyStyle = document.body.style;
		if (bodyStyle.backgroundColor === "black") {
			bodyStyle.backgroundColor = "white";
		} else {
			bodyStyle.backgroundColor = "black";
		}
	}

	return <button on_click={handleClick()}>Toggle the lights</button>;
}
```

<Solution>

The problem is that `<button on_click={handleClick()}>` _calls_ the `handleClick` function while rendering instead of _passing_ it. Removing the `()` call so that it's `<button on_click={handleClick}>` fixes the issue:

```js
export default function LightSwitch() {
	function handleClick() {
		let bodyStyle = document.body.style;
		if (bodyStyle.backgroundColor === "black") {
			bodyStyle.backgroundColor = "white";
		} else {
			bodyStyle.backgroundColor = "black";
		}
	}

	return <button on_click={handleClick}>Toggle the lights</button>;
}
```

Alternatively, you could wrap the call into another function, like `<button on_click={() => handleClick()}>`:

```js
export default function LightSwitch() {
	function handleClick() {
		let bodyStyle = document.body.style;
		if (bodyStyle.backgroundColor === "black") {
			bodyStyle.backgroundColor = "white";
		} else {
			bodyStyle.backgroundColor = "black";
		}
	}

	return <button on_click={() => handleClick()}>Toggle the lights</button>;
}
```

</Solution>

#### Wire up the events

This `ColorSwitch` component renders a button. It's supposed to change the page color. Wire it up to the `onChangeColor` event handler prop it receives from the parent so that clicking the button changes the color.

After you do this, notice that clicking the button also increments the page click counter. Your colleague who wrote the parent component insists that `onChangeColor` does not increment any counters. What else might be happening? Fix it so that clicking the button _only_ changes the color, and does _not_ increment the counter.

```js
export default function ColorSwitch({ onChangeColor }) {
	return <button>Change color</button>;
}
```

```js
import { useState } from "react";
import ColorSwitch from "./ColorSwitch.js";

export default function App() {
	const [clicks, setClicks] = useState(0);

	function handleClickOutside() {
		setClicks((c) => c + 1);
	}

	function getRandomLightColor() {
		let r = 150 + Math.round(100 * Math.random());
		let g = 150 + Math.round(100 * Math.random());
		let b = 150 + Math.round(100 * Math.random());
		return `rgb(${r}, ${g}, ${b})`;
	}

	function handleChangeColor() {
		let bodyStyle = document.body.style;
		bodyStyle.backgroundColor = getRandomLightColor();
	}

	return (
		<div
			style={{ width: "100%", height: "100%" }}
			on_click={handleClickOutside}
		>
			<ColorSwitch onChangeColor={handleChangeColor} />
			<br />
			<br />
			<h2>Clicks on the page: {clicks}</h2>
		</div>
	);
}
```

<Solution>

First, you need to add the event handler, like `<button on_click={onChangeColor}>`.

However, this introduces the problem of the incrementing counter. If `onChangeColor` does not do this, as your colleague insists, then the problem is that this event propagates up, and some handler above does it. To solve this problem, you need to stop the propagation. But don't forget that you should still call `onChangeColor`.

```js
export default function ColorSwitch({ onChangeColor }) {
	return (
		<button
			on_click={(e) => {
				e.stopPropagation();
				onChangeColor();
			}}
		>
			Change color
		</button>
	);
}
```

```js
import { useState } from "react";
import ColorSwitch from "./ColorSwitch.js";

export default function App() {
	const [clicks, setClicks] = useState(0);

	function handleClickOutside() {
		setClicks((c) => c + 1);
	}

	function getRandomLightColor() {
		let r = 150 + Math.round(100 * Math.random());
		let g = 150 + Math.round(100 * Math.random());
		let b = 150 + Math.round(100 * Math.random());
		return `rgb(${r}, ${g}, ${b})`;
	}

	function handleChangeColor() {
		let bodyStyle = document.body.style;
		bodyStyle.backgroundColor = getRandomLightColor();
	}

	return (
		<div
			style={{ width: "100%", height: "100%" }}
			on_click={handleClickOutside}
		>
			<ColorSwitch onChangeColor={handleChangeColor} />
			<br />
			<br />
			<h2>Clicks on the page: {clicks}</h2>
		</div>
	);
}
```

</Solution>

</Challenges>
