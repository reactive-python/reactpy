## Overview

<p class="intro" markdown>

Structuring state well can make a difference between a component that is pleasant to modify and debug, and one that is a constant source of bugs. Here are some tips you should consider when structuring state.

</p>

!!! summary "You will learn"

    -   When to use a single vs multiple state variables
    -   What to avoid when organizing state
    -   How to fix common issues with the state structure

## Principles for structuring state

When you write a component that holds some state, you'll have to make choices about how many state variables to use and what the shape of their data should be. While it's possible to write correct programs even with a suboptimal state structure, there are a few principles that can guide you to make better choices:

1. **Group related state.** If you always update two or more state variables at the same time, consider merging them into a single state variable.
2. **Avoid contradictions in state.** When the state is structured in a way that several pieces of state may contradict and "disagree" with each other, you leave room for mistakes. Try to avoid this.
3. **Avoid redundant state.** If you can calculate some information from the component's props or its existing state variables during rendering, you should not put that information into that component's state.
4. **Avoid duplication in state.** When the same data is duplicated between multiple state variables, or within nested objects, it is difficult to keep them in sync. Reduce duplication when you can.
5. **Avoid deeply nested state.** Deeply hierarchical state is not very convenient to update. When possible, prefer to structure state in a flat way.

The goal behind these principles is to _make state easy to update without introducing mistakes_. Removing redundant and duplicate data from state helps ensure that all its pieces stay in sync. This is similar to how a database engineer might want to ["normalize" the database structure](https://docs.microsoft.com/en-us/office/troubleshoot/access/database-normalization-description) to reduce the chance of bugs. To paraphrase Albert Einstein, **"Make your state as simple as it can be--but no simpler."**

Now let's see how these principles apply in action.

## Group related state

You might sometimes be unsure between using a single or multiple state variables.

Should you do this?

```js
const [x, setX] = useState(0);
const [y, setY] = useState(0);
```

Or this?

```js
const [position, setPosition] = useState({ x: 0, y: 0 });
```

Technically, you can use either of these approaches. But **if some two state variables always change together, it might be a good idea to unify them into a single state variable.** Then you won't forget to always keep them in sync, like in this example where moving the cursor updates both coordinates of the red dot:

```js
import { useState } from "react";

export default function MovingDot() {
	const [position, setPosition] = useState({
		x: 0,
		y: 0,
	});
	return (
		<div
			onPointerMove={(e) => {
				setPosition({
					x: e.clientX,
					y: e.clientY,
				});
			}}
			style={{
				position: "relative",
				width: "100vw",
				height: "100vh",
			}}
		>
			<div
				style={{
					position: "absolute",
					backgroundColor: "red",
					borderRadius: "50%",
					transform: `translate(${position.x}px, ${position.y}px)`,
					left: -10,
					top: -10,
					width: 20,
					height: 20,
				}}
			/>
		</div>
	);
}
```

```css
body {
	margin: 0;
	padding: 0;
	height: 250px;
}
```

Another case where you'll group data into an object or an array is when you don't know how many pieces of state you'll need. For example, it's helpful when you have a form where the user can add custom fields.

<Pitfall>

If your state variable is an object, remember that [you can't update only one field in it](/learn/updating-objects-in-state) without explicitly copying the other fields. For example, you can't do `setPosition({ x: 100 })` in the above example because it would not have the `y` property at all! Instead, if you wanted to set `x` alone, you would either do `setPosition({ ...position, x: 100 })`, or split them into two state variables and do `setX(100)`.

</Pitfall>

## Avoid contradictions in state

Here is a hotel feedback form with `isSending` and `isSent` state variables:

```js
import { useState } from "react";

export default function FeedbackForm() {
	const [text, setText] = useState("");
	const [isSending, setIsSending] = useState(false);
	const [isSent, setIsSent] = useState(false);

	async function handleSubmit(e) {
		e.preventDefault();
		setIsSending(true);
		await sendMessage(text);
		setIsSending(false);
		setIsSent(true);
	}

	if (isSent) {
		return <h1>Thanks for feedback!</h1>;
	}

	return (
		<form onSubmit={handleSubmit}>
			<p>How was your stay at The Prancing Pony?</p>
			<textarea
				disabled={isSending}
				value={text}
				onChange={(e) => setText(e.target.value)}
			/>
			<br />
			<button disabled={isSending} type="submit">
				Send
			</button>
			{isSending && <p>Sending...</p>}
		</form>
	);
}

// Pretend to send a message.
function sendMessage(text) {
	return new Promise((resolve) => {
		setTimeout(resolve, 2000);
	});
}
```

While this code works, it leaves the door open for "impossible" states. For example, if you forget to call `setIsSent` and `setIsSending` together, you may end up in a situation where both `isSending` and `isSent` are `true` at the same time. The more complex your component is, the harder it is to understand what happened.

**Since `isSending` and `isSent` should never be `true` at the same time, it is better to replace them with one `status` state variable that may take one of _three_ valid states:** `'typing'` (initial), `'sending'`, and `'sent'`:

```js
import { useState } from "react";

export default function FeedbackForm() {
	const [text, setText] = useState("");
	const [status, setStatus] = useState("typing");

	async function handleSubmit(e) {
		e.preventDefault();
		setStatus("sending");
		await sendMessage(text);
		setStatus("sent");
	}

	const isSending = status === "sending";
	const isSent = status === "sent";

	if (isSent) {
		return <h1>Thanks for feedback!</h1>;
	}

	return (
		<form onSubmit={handleSubmit}>
			<p>How was your stay at The Prancing Pony?</p>
			<textarea
				disabled={isSending}
				value={text}
				onChange={(e) => setText(e.target.value)}
			/>
			<br />
			<button disabled={isSending} type="submit">
				Send
			</button>
			{isSending && <p>Sending...</p>}
		</form>
	);
}

// Pretend to send a message.
function sendMessage(text) {
	return new Promise((resolve) => {
		setTimeout(resolve, 2000);
	});
}
```

You can still declare some constants for readability:

```js
const isSending = status === "sending";
const isSent = status === "sent";
```

But they're not state variables, so you don't need to worry about them getting out of sync with each other.

## Avoid redundant state

If you can calculate some information from the component's props or its existing state variables during rendering, you **should not** put that information into that component's state.

For example, take this form. It works, but can you find any redundant state in it?

```js
import { useState } from "react";

export default function Form() {
	const [firstName, setFirstName] = useState("");
	const [lastName, setLastName] = useState("");
	const [fullName, setFullName] = useState("");

	function handleFirstNameChange(e) {
		setFirstName(e.target.value);
		setFullName(e.target.value + " " + lastName);
	}

	function handleLastNameChange(e) {
		setLastName(e.target.value);
		setFullName(firstName + " " + e.target.value);
	}

	return (
		<>
			<h2>Let’s check you in</h2>
			<label>
				First name:{" "}
				<input value={firstName} onChange={handleFirstNameChange} />
			</label>
			<label>
				Last name:{" "}
				<input value={lastName} onChange={handleLastNameChange} />
			</label>
			<p>
				Your ticket will be issued to: <b>{fullName}</b>
			</p>
		</>
	);
}
```

```css
label {
	display: block;
	margin-bottom: 5px;
}
```

This form has three state variables: `firstName`, `lastName`, and `fullName`. However, `fullName` is redundant. **You can always calculate `fullName` from `firstName` and `lastName` during render, so remove it from state.**

This is how you can do it:

```js
import { useState } from "react";

export default function Form() {
	const [firstName, setFirstName] = useState("");
	const [lastName, setLastName] = useState("");

	const fullName = firstName + " " + lastName;

	function handleFirstNameChange(e) {
		setFirstName(e.target.value);
	}

	function handleLastNameChange(e) {
		setLastName(e.target.value);
	}

	return (
		<>
			<h2>Let’s check you in</h2>
			<label>
				First name:{" "}
				<input value={firstName} onChange={handleFirstNameChange} />
			</label>
			<label>
				Last name:{" "}
				<input value={lastName} onChange={handleLastNameChange} />
			</label>
			<p>
				Your ticket will be issued to: <b>{fullName}</b>
			</p>
		</>
	);
}
```

```css
label {
	display: block;
	margin-bottom: 5px;
}
```

Here, `fullName` is _not_ a state variable. Instead, it's calculated during render:

```js
const fullName = firstName + " " + lastName;
```

As a result, the change handlers don't need to do anything special to update it. When you call `setFirstName` or `setLastName`, you trigger a re-render, and then the next `fullName` will be calculated from the fresh data.

<DeepDive>

#### Don't mirror props in state

A common example of redundant state is code like this:

```js
function Message({ messageColor }) {
  const [color, setColor] = useState(messageColor);
```

Here, a `color` state variable is initialized to the `messageColor` prop. The problem is that **if the parent component passes a different value of `messageColor` later (for example, `'red'` instead of `'blue'`), the `color` _state variable_ would not be updated!** The state is only initialized during the first render.

This is why "mirroring" some prop in a state variable can lead to confusion. Instead, use the `messageColor` prop directly in your code. If you want to give it a shorter name, use a constant:

```js
function Message({ messageColor }) {
  const color = messageColor;
```

This way it won't get out of sync with the prop passed from the parent component.

"Mirroring" props into state only makes sense when you _want_ to ignore all updates for a specific prop. By convention, start the prop name with `initial` or `default` to clarify that its new values are ignored:

```js
function Message({ initialColor }) {
  // The `color` state variable holds the *first* value of `initialColor`.
  // Further changes to the `initialColor` prop are ignored.
  const [color, setColor] = useState(initialColor);
```

</DeepDive>

## Avoid duplication in state

This menu list component lets you choose a single travel snack out of several:

```js
import { useState } from "react";

const initialItems = [
	{ title: "pretzels", id: 0 },
	{ title: "crispy seaweed", id: 1 },
	{ title: "granola bar", id: 2 },
];

export default function Menu() {
	const [items, setItems] = useState(initialItems);
	const [selectedItem, setSelectedItem] = useState(items[0]);

	return (
		<>
			<h2>What's your travel snack?</h2>
			<ul>
				{items.map((item) => (
					<li key={item.id}>
						{item.title}{" "}
						<button
							on_click={() => {
								setSelectedItem(item);
							}}
						>
							Choose
						</button>
					</li>
				))}
			</ul>
			<p>You picked {selectedItem.title}.</p>
		</>
	);
}
```

```css
button {
	margin-top: 10px;
}
```

Currently, it stores the selected item as an object in the `selectedItem` state variable. However, this is not great: **the contents of the `selectedItem` is the same object as one of the items inside the `items` list.** This means that the information about the item itself is duplicated in two places.

Why is this a problem? Let's make each item editable:

```js
import { useState } from "react";

const initialItems = [
	{ title: "pretzels", id: 0 },
	{ title: "crispy seaweed", id: 1 },
	{ title: "granola bar", id: 2 },
];

export default function Menu() {
	const [items, setItems] = useState(initialItems);
	const [selectedItem, setSelectedItem] = useState(items[0]);

	function handleItemChange(id, e) {
		setItems(
			items.map((item) => {
				if (item.id === id) {
					return {
						...item,
						title: e.target.value,
					};
				} else {
					return item;
				}
			})
		);
	}

	return (
		<>
			<h2>What's your travel snack?</h2>
			<ul>
				{items.map((item, index) => (
					<li key={item.id}>
						<input
							value={item.title}
							onChange={(e) => {
								handleItemChange(item.id, e);
							}}
						/>{" "}
						<button
							on_click={() => {
								setSelectedItem(item);
							}}
						>
							Choose
						</button>
					</li>
				))}
			</ul>
			<p>You picked {selectedItem.title}.</p>
		</>
	);
}
```

```css
button {
	margin-top: 10px;
}
```

Notice how if you first click "Choose" on an item and _then_ edit it, **the input updates but the label at the bottom does not reflect the edits.** This is because you have duplicated state, and you forgot to update `selectedItem`.

Although you could update `selectedItem` too, an easier fix is to remove duplication. In this example, instead of a `selectedItem` object (which creates a duplication with objects inside `items`), you hold the `selectedId` in state, and _then_ get the `selectedItem` by searching the `items` array for an item with that ID:

```js
import { useState } from "react";

const initialItems = [
	{ title: "pretzels", id: 0 },
	{ title: "crispy seaweed", id: 1 },
	{ title: "granola bar", id: 2 },
];

export default function Menu() {
	const [items, setItems] = useState(initialItems);
	const [selectedId, setSelectedId] = useState(0);

	const selectedItem = items.find((item) => item.id === selectedId);

	function handleItemChange(id, e) {
		setItems(
			items.map((item) => {
				if (item.id === id) {
					return {
						...item,
						title: e.target.value,
					};
				} else {
					return item;
				}
			})
		);
	}

	return (
		<>
			<h2>What's your travel snack?</h2>
			<ul>
				{items.map((item, index) => (
					<li key={item.id}>
						<input
							value={item.title}
							onChange={(e) => {
								handleItemChange(item.id, e);
							}}
						/>{" "}
						<button
							on_click={() => {
								setSelectedId(item.id);
							}}
						>
							Choose
						</button>
					</li>
				))}
			</ul>
			<p>You picked {selectedItem.title}.</p>
		</>
	);
}
```

```css
button {
	margin-top: 10px;
}
```

(Alternatively, you may hold the selected index in state.)

The state used to be duplicated like this:

-   `items = [{ id: 0, title: 'pretzels'}, ...]`
-   `selectedItem = {id: 0, title: 'pretzels'}`

But after the change it's like this:

-   `items = [{ id: 0, title: 'pretzels'}, ...]`
-   `selectedId = 0`

The duplication is gone, and you only keep the essential state!

Now if you edit the _selected_ item, the message below will update immediately. This is because `setItems` triggers a re-render, and `items.find(...)` would find the item with the updated title. You didn't need to hold _the selected item_ in state, because only the _selected ID_ is essential. The rest could be calculated during render.

## Avoid deeply nested state

Imagine a travel plan consisting of planets, continents, and countries. You might be tempted to structure its state using nested objects and arrays, like in this example:

```js
import { useState } from "react";
import { initialTravelPlan } from "./places.js";

function PlaceTree({ place }) {
	const childPlaces = place.childPlaces;
	return (
		<li>
			{place.title}
			{childPlaces.length > 0 && (
				<ol>
					{childPlaces.map((place) => (
						<PlaceTree key={place.id} place={place} />
					))}
				</ol>
			)}
		</li>
	);
}

export default function TravelPlan() {
	const [plan, setPlan] = useState(initialTravelPlan);
	const planets = plan.childPlaces;
	return (
		<>
			<h2>Places to visit</h2>
			<ol>
				{planets.map((place) => (
					<PlaceTree key={place.id} place={place} />
				))}
			</ol>
		</>
	);
}
```

```js
export const initialTravelPlan = {
	id: 0,
	title: "(Root)",
	childPlaces: [
		{
			id: 1,
			title: "Earth",
			childPlaces: [
				{
					id: 2,
					title: "Africa",
					childPlaces: [
						{
							id: 3,
							title: "Botswana",
							childPlaces: [],
						},
						{
							id: 4,
							title: "Egypt",
							childPlaces: [],
						},
						{
							id: 5,
							title: "Kenya",
							childPlaces: [],
						},
						{
							id: 6,
							title: "Madagascar",
							childPlaces: [],
						},
						{
							id: 7,
							title: "Morocco",
							childPlaces: [],
						},
						{
							id: 8,
							title: "Nigeria",
							childPlaces: [],
						},
						{
							id: 9,
							title: "South Africa",
							childPlaces: [],
						},
					],
				},
				{
					id: 10,
					title: "Americas",
					childPlaces: [
						{
							id: 11,
							title: "Argentina",
							childPlaces: [],
						},
						{
							id: 12,
							title: "Brazil",
							childPlaces: [],
						},
						{
							id: 13,
							title: "Barbados",
							childPlaces: [],
						},
						{
							id: 14,
							title: "Canada",
							childPlaces: [],
						},
						{
							id: 15,
							title: "Jamaica",
							childPlaces: [],
						},
						{
							id: 16,
							title: "Mexico",
							childPlaces: [],
						},
						{
							id: 17,
							title: "Trinidad and Tobago",
							childPlaces: [],
						},
						{
							id: 18,
							title: "Venezuela",
							childPlaces: [],
						},
					],
				},
				{
					id: 19,
					title: "Asia",
					childPlaces: [
						{
							id: 20,
							title: "China",
							childPlaces: [],
						},
						{
							id: 21,
							title: "Hong Kong",
							childPlaces: [],
						},
						{
							id: 22,
							title: "India",
							childPlaces: [],
						},
						{
							id: 23,
							title: "Singapore",
							childPlaces: [],
						},
						{
							id: 24,
							title: "South Korea",
							childPlaces: [],
						},
						{
							id: 25,
							title: "Thailand",
							childPlaces: [],
						},
						{
							id: 26,
							title: "Vietnam",
							childPlaces: [],
						},
					],
				},
				{
					id: 27,
					title: "Europe",
					childPlaces: [
						{
							id: 28,
							title: "Croatia",
							childPlaces: [],
						},
						{
							id: 29,
							title: "France",
							childPlaces: [],
						},
						{
							id: 30,
							title: "Germany",
							childPlaces: [],
						},
						{
							id: 31,
							title: "Italy",
							childPlaces: [],
						},
						{
							id: 32,
							title: "Portugal",
							childPlaces: [],
						},
						{
							id: 33,
							title: "Spain",
							childPlaces: [],
						},
						{
							id: 34,
							title: "Turkey",
							childPlaces: [],
						},
					],
				},
				{
					id: 35,
					title: "Oceania",
					childPlaces: [
						{
							id: 36,
							title: "Australia",
							childPlaces: [],
						},
						{
							id: 37,
							title: "Bora Bora (French Polynesia)",
							childPlaces: [],
						},
						{
							id: 38,
							title: "Easter Island (Chile)",
							childPlaces: [],
						},
						{
							id: 39,
							title: "Fiji",
							childPlaces: [],
						},
						{
							id: 40,
							title: "Hawaii (the USA)",
							childPlaces: [],
						},
						{
							id: 41,
							title: "New Zealand",
							childPlaces: [],
						},
						{
							id: 42,
							title: "Vanuatu",
							childPlaces: [],
						},
					],
				},
			],
		},
		{
			id: 43,
			title: "Moon",
			childPlaces: [
				{
					id: 44,
					title: "Rheita",
					childPlaces: [],
				},
				{
					id: 45,
					title: "Piccolomini",
					childPlaces: [],
				},
				{
					id: 46,
					title: "Tycho",
					childPlaces: [],
				},
			],
		},
		{
			id: 47,
			title: "Mars",
			childPlaces: [
				{
					id: 48,
					title: "Corn Town",
					childPlaces: [],
				},
				{
					id: 49,
					title: "Green Hill",
					childPlaces: [],
				},
			],
		},
	],
};
```

Now let's say you want to add a button to delete a place you've already visited. How would you go about it? [Updating nested state](/learn/updating-objects-in-state#updating-a-nested-object) involves making copies of objects all the way up from the part that changed. Deleting a deeply nested place would involve copying its entire parent place chain. Such code can be very verbose.

**If the state is too nested to update easily, consider making it "flat".** Here is one way you can restructure this data. Instead of a tree-like structure where each `place` has an array of _its child places_, you can have each place hold an array of _its child place IDs_. Then store a mapping from each place ID to the corresponding place.

This data restructuring might remind you of seeing a database table:

```js
import { useState } from "react";
import { initialTravelPlan } from "./places.js";

function PlaceTree({ id, placesById }) {
	const place = placesById[id];
	const childIds = place.childIds;
	return (
		<li>
			{place.title}
			{childIds.length > 0 && (
				<ol>
					{childIds.map((childId) => (
						<PlaceTree
							key={childId}
							id={childId}
							placesById={placesById}
						/>
					))}
				</ol>
			)}
		</li>
	);
}

export default function TravelPlan() {
	const [plan, setPlan] = useState(initialTravelPlan);
	const root = plan[0];
	const planetIds = root.childIds;
	return (
		<>
			<h2>Places to visit</h2>
			<ol>
				{planetIds.map((id) => (
					<PlaceTree key={id} id={id} placesById={plan} />
				))}
			</ol>
		</>
	);
}
```

```js
export const initialTravelPlan = {
	0: {
		id: 0,
		title: "(Root)",
		childIds: [1, 43, 47],
	},
	1: {
		id: 1,
		title: "Earth",
		childIds: [2, 10, 19, 27, 35],
	},
	2: {
		id: 2,
		title: "Africa",
		childIds: [3, 4, 5, 6, 7, 8, 9],
	},
	3: {
		id: 3,
		title: "Botswana",
		childIds: [],
	},
	4: {
		id: 4,
		title: "Egypt",
		childIds: [],
	},
	5: {
		id: 5,
		title: "Kenya",
		childIds: [],
	},
	6: {
		id: 6,
		title: "Madagascar",
		childIds: [],
	},
	7: {
		id: 7,
		title: "Morocco",
		childIds: [],
	},
	8: {
		id: 8,
		title: "Nigeria",
		childIds: [],
	},
	9: {
		id: 9,
		title: "South Africa",
		childIds: [],
	},
	10: {
		id: 10,
		title: "Americas",
		childIds: [11, 12, 13, 14, 15, 16, 17, 18],
	},
	11: {
		id: 11,
		title: "Argentina",
		childIds: [],
	},
	12: {
		id: 12,
		title: "Brazil",
		childIds: [],
	},
	13: {
		id: 13,
		title: "Barbados",
		childIds: [],
	},
	14: {
		id: 14,
		title: "Canada",
		childIds: [],
	},
	15: {
		id: 15,
		title: "Jamaica",
		childIds: [],
	},
	16: {
		id: 16,
		title: "Mexico",
		childIds: [],
	},
	17: {
		id: 17,
		title: "Trinidad and Tobago",
		childIds: [],
	},
	18: {
		id: 18,
		title: "Venezuela",
		childIds: [],
	},
	19: {
		id: 19,
		title: "Asia",
		childIds: [20, 21, 22, 23, 24, 25, 26],
	},
	20: {
		id: 20,
		title: "China",
		childIds: [],
	},
	21: {
		id: 21,
		title: "Hong Kong",
		childIds: [],
	},
	22: {
		id: 22,
		title: "India",
		childIds: [],
	},
	23: {
		id: 23,
		title: "Singapore",
		childIds: [],
	},
	24: {
		id: 24,
		title: "South Korea",
		childIds: [],
	},
	25: {
		id: 25,
		title: "Thailand",
		childIds: [],
	},
	26: {
		id: 26,
		title: "Vietnam",
		childIds: [],
	},
	27: {
		id: 27,
		title: "Europe",
		childIds: [28, 29, 30, 31, 32, 33, 34],
	},
	28: {
		id: 28,
		title: "Croatia",
		childIds: [],
	},
	29: {
		id: 29,
		title: "France",
		childIds: [],
	},
	30: {
		id: 30,
		title: "Germany",
		childIds: [],
	},
	31: {
		id: 31,
		title: "Italy",
		childIds: [],
	},
	32: {
		id: 32,
		title: "Portugal",
		childIds: [],
	},
	33: {
		id: 33,
		title: "Spain",
		childIds: [],
	},
	34: {
		id: 34,
		title: "Turkey",
		childIds: [],
	},
	35: {
		id: 35,
		title: "Oceania",
		childIds: [36, 37, 38, 39, 40, 41, 42],
	},
	36: {
		id: 36,
		title: "Australia",
		childIds: [],
	},
	37: {
		id: 37,
		title: "Bora Bora (French Polynesia)",
		childIds: [],
	},
	38: {
		id: 38,
		title: "Easter Island (Chile)",
		childIds: [],
	},
	39: {
		id: 39,
		title: "Fiji",
		childIds: [],
	},
	40: {
		id: 40,
		title: "Hawaii (the USA)",
		childIds: [],
	},
	41: {
		id: 41,
		title: "New Zealand",
		childIds: [],
	},
	42: {
		id: 42,
		title: "Vanuatu",
		childIds: [],
	},
	43: {
		id: 43,
		title: "Moon",
		childIds: [44, 45, 46],
	},
	44: {
		id: 44,
		title: "Rheita",
		childIds: [],
	},
	45: {
		id: 45,
		title: "Piccolomini",
		childIds: [],
	},
	46: {
		id: 46,
		title: "Tycho",
		childIds: [],
	},
	47: {
		id: 47,
		title: "Mars",
		childIds: [48, 49],
	},
	48: {
		id: 48,
		title: "Corn Town",
		childIds: [],
	},
	49: {
		id: 49,
		title: "Green Hill",
		childIds: [],
	},
};
```

**Now that the state is "flat" (also known as "normalized"), updating nested items becomes easier.**

In order to remove a place now, you only need to update two levels of state:

-   The updated version of its _parent_ place should exclude the removed ID from its `childIds` array.
-   The updated version of the root "table" object should include the updated version of the parent place.

Here is an example of how you could go about it:

```js
import { useState } from "react";
import { initialTravelPlan } from "./places.js";

export default function TravelPlan() {
	const [plan, setPlan] = useState(initialTravelPlan);

	function handleComplete(parentId, childId) {
		const parent = plan[parentId];
		// Create a new version of the parent place
		// that doesn't include this child ID.
		const nextParent = {
			...parent,
			childIds: parent.childIds.filter((id) => id !== childId),
		};
		// Update the root state object...
		setPlan({
			...plan,
			// ...so that it has the updated parent.
			[parentId]: nextParent,
		});
	}

	const root = plan[0];
	const planetIds = root.childIds;
	return (
		<>
			<h2>Places to visit</h2>
			<ol>
				{planetIds.map((id) => (
					<PlaceTree
						key={id}
						id={id}
						parentId={0}
						placesById={plan}
						onComplete={handleComplete}
					/>
				))}
			</ol>
		</>
	);
}

function PlaceTree({ id, parentId, placesById, onComplete }) {
	const place = placesById[id];
	const childIds = place.childIds;
	return (
		<li>
			{place.title}
			<button
				on_click={() => {
					onComplete(parentId, id);
				}}
			>
				Complete
			</button>
			{childIds.length > 0 && (
				<ol>
					{childIds.map((childId) => (
						<PlaceTree
							key={childId}
							id={childId}
							parentId={id}
							placesById={placesById}
							onComplete={onComplete}
						/>
					))}
				</ol>
			)}
		</li>
	);
}
```

```js
export const initialTravelPlan = {
	0: {
		id: 0,
		title: "(Root)",
		childIds: [1, 43, 47],
	},
	1: {
		id: 1,
		title: "Earth",
		childIds: [2, 10, 19, 27, 35],
	},
	2: {
		id: 2,
		title: "Africa",
		childIds: [3, 4, 5, 6, 7, 8, 9],
	},
	3: {
		id: 3,
		title: "Botswana",
		childIds: [],
	},
	4: {
		id: 4,
		title: "Egypt",
		childIds: [],
	},
	5: {
		id: 5,
		title: "Kenya",
		childIds: [],
	},
	6: {
		id: 6,
		title: "Madagascar",
		childIds: [],
	},
	7: {
		id: 7,
		title: "Morocco",
		childIds: [],
	},
	8: {
		id: 8,
		title: "Nigeria",
		childIds: [],
	},
	9: {
		id: 9,
		title: "South Africa",
		childIds: [],
	},
	10: {
		id: 10,
		title: "Americas",
		childIds: [11, 12, 13, 14, 15, 16, 17, 18],
	},
	11: {
		id: 11,
		title: "Argentina",
		childIds: [],
	},
	12: {
		id: 12,
		title: "Brazil",
		childIds: [],
	},
	13: {
		id: 13,
		title: "Barbados",
		childIds: [],
	},
	14: {
		id: 14,
		title: "Canada",
		childIds: [],
	},
	15: {
		id: 15,
		title: "Jamaica",
		childIds: [],
	},
	16: {
		id: 16,
		title: "Mexico",
		childIds: [],
	},
	17: {
		id: 17,
		title: "Trinidad and Tobago",
		childIds: [],
	},
	18: {
		id: 18,
		title: "Venezuela",
		childIds: [],
	},
	19: {
		id: 19,
		title: "Asia",
		childIds: [20, 21, 22, 23, 24, 25, 26],
	},
	20: {
		id: 20,
		title: "China",
		childIds: [],
	},
	21: {
		id: 21,
		title: "Hong Kong",
		childIds: [],
	},
	22: {
		id: 22,
		title: "India",
		childIds: [],
	},
	23: {
		id: 23,
		title: "Singapore",
		childIds: [],
	},
	24: {
		id: 24,
		title: "South Korea",
		childIds: [],
	},
	25: {
		id: 25,
		title: "Thailand",
		childIds: [],
	},
	26: {
		id: 26,
		title: "Vietnam",
		childIds: [],
	},
	27: {
		id: 27,
		title: "Europe",
		childIds: [28, 29, 30, 31, 32, 33, 34],
	},
	28: {
		id: 28,
		title: "Croatia",
		childIds: [],
	},
	29: {
		id: 29,
		title: "France",
		childIds: [],
	},
	30: {
		id: 30,
		title: "Germany",
		childIds: [],
	},
	31: {
		id: 31,
		title: "Italy",
		childIds: [],
	},
	32: {
		id: 32,
		title: "Portugal",
		childIds: [],
	},
	33: {
		id: 33,
		title: "Spain",
		childIds: [],
	},
	34: {
		id: 34,
		title: "Turkey",
		childIds: [],
	},
	35: {
		id: 35,
		title: "Oceania",
		childIds: [36, 37, 38, 39, 40, 41, , 42],
	},
	36: {
		id: 36,
		title: "Australia",
		childIds: [],
	},
	37: {
		id: 37,
		title: "Bora Bora (French Polynesia)",
		childIds: [],
	},
	38: {
		id: 38,
		title: "Easter Island (Chile)",
		childIds: [],
	},
	39: {
		id: 39,
		title: "Fiji",
		childIds: [],
	},
	40: {
		id: 40,
		title: "Hawaii (the USA)",
		childIds: [],
	},
	41: {
		id: 41,
		title: "New Zealand",
		childIds: [],
	},
	42: {
		id: 42,
		title: "Vanuatu",
		childIds: [],
	},
	43: {
		id: 43,
		title: "Moon",
		childIds: [44, 45, 46],
	},
	44: {
		id: 44,
		title: "Rheita",
		childIds: [],
	},
	45: {
		id: 45,
		title: "Piccolomini",
		childIds: [],
	},
	46: {
		id: 46,
		title: "Tycho",
		childIds: [],
	},
	47: {
		id: 47,
		title: "Mars",
		childIds: [48, 49],
	},
	48: {
		id: 48,
		title: "Corn Town",
		childIds: [],
	},
	49: {
		id: 49,
		title: "Green Hill",
		childIds: [],
	},
};
```

```css
button {
	margin: 10px;
}
```

You can nest state as much as you like, but making it "flat" can solve numerous problems. It makes state easier to update, and it helps ensure you don't have duplication in different parts of a nested object.

<DeepDive>

#### Improving memory usage

Ideally, you would also remove the deleted items (and their children!) from the "table" object to improve memory usage. This version does that. It also [uses Immer](/learn/updating-objects-in-state#write-concise-update-logic-with-immer) to make the update logic more concise.

```js
import { useImmer } from "use-immer";
import { initialTravelPlan } from "./places.js";

export default function TravelPlan() {
	const [plan, updatePlan] = useImmer(initialTravelPlan);

	function handleComplete(parentId, childId) {
		updatePlan((draft) => {
			// Remove from the parent place's child IDs.
			const parent = draft[parentId];
			parent.childIds = parent.childIds.filter((id) => id !== childId);

			// Forget this place and all its subtree.
			deleteAllChildren(childId);
			function deleteAllChildren(id) {
				const place = draft[id];
				place.childIds.forEach(deleteAllChildren);
				delete draft[id];
			}
		});
	}

	const root = plan[0];
	const planetIds = root.childIds;
	return (
		<>
			<h2>Places to visit</h2>
			<ol>
				{planetIds.map((id) => (
					<PlaceTree
						key={id}
						id={id}
						parentId={0}
						placesById={plan}
						onComplete={handleComplete}
					/>
				))}
			</ol>
		</>
	);
}

function PlaceTree({ id, parentId, placesById, onComplete }) {
	const place = placesById[id];
	const childIds = place.childIds;
	return (
		<li>
			{place.title}
			<button
				on_click={() => {
					onComplete(parentId, id);
				}}
			>
				Complete
			</button>
			{childIds.length > 0 && (
				<ol>
					{childIds.map((childId) => (
						<PlaceTree
							key={childId}
							id={childId}
							parentId={id}
							placesById={placesById}
							onComplete={onComplete}
						/>
					))}
				</ol>
			)}
		</li>
	);
}
```

```js
export const initialTravelPlan = {
	0: {
		id: 0,
		title: "(Root)",
		childIds: [1, 43, 47],
	},
	1: {
		id: 1,
		title: "Earth",
		childIds: [2, 10, 19, 27, 35],
	},
	2: {
		id: 2,
		title: "Africa",
		childIds: [3, 4, 5, 6, 7, 8, 9],
	},
	3: {
		id: 3,
		title: "Botswana",
		childIds: [],
	},
	4: {
		id: 4,
		title: "Egypt",
		childIds: [],
	},
	5: {
		id: 5,
		title: "Kenya",
		childIds: [],
	},
	6: {
		id: 6,
		title: "Madagascar",
		childIds: [],
	},
	7: {
		id: 7,
		title: "Morocco",
		childIds: [],
	},
	8: {
		id: 8,
		title: "Nigeria",
		childIds: [],
	},
	9: {
		id: 9,
		title: "South Africa",
		childIds: [],
	},
	10: {
		id: 10,
		title: "Americas",
		childIds: [11, 12, 13, 14, 15, 16, 17, 18],
	},
	11: {
		id: 11,
		title: "Argentina",
		childIds: [],
	},
	12: {
		id: 12,
		title: "Brazil",
		childIds: [],
	},
	13: {
		id: 13,
		title: "Barbados",
		childIds: [],
	},
	14: {
		id: 14,
		title: "Canada",
		childIds: [],
	},
	15: {
		id: 15,
		title: "Jamaica",
		childIds: [],
	},
	16: {
		id: 16,
		title: "Mexico",
		childIds: [],
	},
	17: {
		id: 17,
		title: "Trinidad and Tobago",
		childIds: [],
	},
	18: {
		id: 18,
		title: "Venezuela",
		childIds: [],
	},
	19: {
		id: 19,
		title: "Asia",
		childIds: [20, 21, 22, 23, 24, 25, 26],
	},
	20: {
		id: 20,
		title: "China",
		childIds: [],
	},
	21: {
		id: 21,
		title: "Hong Kong",
		childIds: [],
	},
	22: {
		id: 22,
		title: "India",
		childIds: [],
	},
	23: {
		id: 23,
		title: "Singapore",
		childIds: [],
	},
	24: {
		id: 24,
		title: "South Korea",
		childIds: [],
	},
	25: {
		id: 25,
		title: "Thailand",
		childIds: [],
	},
	26: {
		id: 26,
		title: "Vietnam",
		childIds: [],
	},
	27: {
		id: 27,
		title: "Europe",
		childIds: [28, 29, 30, 31, 32, 33, 34],
	},
	28: {
		id: 28,
		title: "Croatia",
		childIds: [],
	},
	29: {
		id: 29,
		title: "France",
		childIds: [],
	},
	30: {
		id: 30,
		title: "Germany",
		childIds: [],
	},
	31: {
		id: 31,
		title: "Italy",
		childIds: [],
	},
	32: {
		id: 32,
		title: "Portugal",
		childIds: [],
	},
	33: {
		id: 33,
		title: "Spain",
		childIds: [],
	},
	34: {
		id: 34,
		title: "Turkey",
		childIds: [],
	},
	35: {
		id: 35,
		title: "Oceania",
		childIds: [36, 37, 38, 39, 40, 41, , 42],
	},
	36: {
		id: 36,
		title: "Australia",
		childIds: [],
	},
	37: {
		id: 37,
		title: "Bora Bora (French Polynesia)",
		childIds: [],
	},
	38: {
		id: 38,
		title: "Easter Island (Chile)",
		childIds: [],
	},
	39: {
		id: 39,
		title: "Fiji",
		childIds: [],
	},
	40: {
		id: 40,
		title: "Hawaii (the USA)",
		childIds: [],
	},
	41: {
		id: 41,
		title: "New Zealand",
		childIds: [],
	},
	42: {
		id: 42,
		title: "Vanuatu",
		childIds: [],
	},
	43: {
		id: 43,
		title: "Moon",
		childIds: [44, 45, 46],
	},
	44: {
		id: 44,
		title: "Rheita",
		childIds: [],
	},
	45: {
		id: 45,
		title: "Piccolomini",
		childIds: [],
	},
	46: {
		id: 46,
		title: "Tycho",
		childIds: [],
	},
	47: {
		id: 47,
		title: "Mars",
		childIds: [48, 49],
	},
	48: {
		id: 48,
		title: "Corn Town",
		childIds: [],
	},
	49: {
		id: 49,
		title: "Green Hill",
		childIds: [],
	},
};
```

```css
button {
	margin: 10px;
}
```

```json
{
	"dependencies": {
		"immer": "1.7.3",
		"react": "latest",
		"react-dom": "latest",
		"react-scripts": "latest",
		"use-immer": "0.5.1"
	},
	"scripts": {
		"start": "react-scripts start",
		"build": "react-scripts build",
		"test": "react-scripts test --env=jsdom",
		"eject": "react-scripts eject"
	}
}
```

</DeepDive>

Sometimes, you can also reduce state nesting by moving some of the nested state into the child components. This works well for ephemeral UI state that doesn't need to be stored, like whether an item is hovered.

<Recap>

-   If two state variables always update together, consider merging them into one.
-   Choose your state variables carefully to avoid creating "impossible" states.
-   Structure your state in a way that reduces the chances that you'll make a mistake updating it.
-   Avoid redundant and duplicate state so that you don't need to keep it in sync.
-   Don't put props _into_ state unless you specifically want to prevent updates.
-   For UI patterns like selection, keep ID or index in state instead of the object itself.
-   If updating deeply nested state is complicated, try flattening it.

</Recap>

<Challenges>

#### Fix a component that's not updating

This `Clock` component receives two props: `color` and `time`. When you select a different color in the select box, the `Clock` component receives a different `color` prop from its parent component. However, for some reason, the displayed color doesn't update. Why? Fix the problem.

```js
import { useState } from "react";

export default function Clock(props) {
	const [color, setColor] = useState(props.color);
	return <h1 style={{ color: color }}>{props.time}</h1>;
}
```

```js
import { useState, useEffect } from "react";
import Clock from "./Clock.js";

function useTime() {
	const [time, setTime] = useState(() => new Date());
	useEffect(() => {
		const id = setInterval(() => {
			setTime(new Date());
		}, 1000);
		return () => clearInterval(id);
	}, []);
	return time;
}

export default function App() {
	const time = useTime();
	const [color, setColor] = useState("lightcoral");
	return (
		<div>
			<p>
				Pick a color:{" "}
				<select
					value={color}
					onChange={(e) => setColor(e.target.value)}
				>
					<option value="lightcoral">lightcoral</option>
					<option value="midnightblue">midnightblue</option>
					<option value="rebeccapurple">rebeccapurple</option>
				</select>
			</p>
			<Clock color={color} time={time.toLocaleTimeString()} />
		</div>
	);
}
```

<Solution>

The issue is that this component has `color` state initialized with the initial value of the `color` prop. But when the `color` prop changes, this does not affect the state variable! So they get out of sync. To fix this issue, remove the state variable altogether, and use the `color` prop directly.

```js
import { useState } from "react";

export default function Clock(props) {
	return <h1 style={{ color: props.color }}>{props.time}</h1>;
}
```

```js
import { useState, useEffect } from "react";
import Clock from "./Clock.js";

function useTime() {
	const [time, setTime] = useState(() => new Date());
	useEffect(() => {
		const id = setInterval(() => {
			setTime(new Date());
		}, 1000);
		return () => clearInterval(id);
	}, []);
	return time;
}

export default function App() {
	const time = useTime();
	const [color, setColor] = useState("lightcoral");
	return (
		<div>
			<p>
				Pick a color:{" "}
				<select
					value={color}
					onChange={(e) => setColor(e.target.value)}
				>
					<option value="lightcoral">lightcoral</option>
					<option value="midnightblue">midnightblue</option>
					<option value="rebeccapurple">rebeccapurple</option>
				</select>
			</p>
			<Clock color={color} time={time.toLocaleTimeString()} />
		</div>
	);
}
```

Or, using the destructuring syntax:

```js
import { useState } from "react";

export default function Clock({ color, time }) {
	return <h1 style={{ color: color }}>{time}</h1>;
}
```

```js
import { useState, useEffect } from "react";
import Clock from "./Clock.js";

function useTime() {
	const [time, setTime] = useState(() => new Date());
	useEffect(() => {
		const id = setInterval(() => {
			setTime(new Date());
		}, 1000);
		return () => clearInterval(id);
	}, []);
	return time;
}

export default function App() {
	const time = useTime();
	const [color, setColor] = useState("lightcoral");
	return (
		<div>
			<p>
				Pick a color:{" "}
				<select
					value={color}
					onChange={(e) => setColor(e.target.value)}
				>
					<option value="lightcoral">lightcoral</option>
					<option value="midnightblue">midnightblue</option>
					<option value="rebeccapurple">rebeccapurple</option>
				</select>
			</p>
			<Clock color={color} time={time.toLocaleTimeString()} />
		</div>
	);
}
```

</Solution>

#### Fix a broken packing list

This packing list has a footer that shows how many items are packed, and how many items there are overall. It seems to work at first, but it is buggy. For example, if you mark an item as packed and then delete it, the counter will not be updated correctly. Fix the counter so that it's always correct.

<Hint>

Is any state in this example redundant?

</Hint>

```js
import { useState } from "react";
import AddItem from "./AddItem.js";
import PackingList from "./PackingList.js";

let nextId = 3;
const initialItems = [
	{ id: 0, title: "Warm socks", packed: true },
	{ id: 1, title: "Travel journal", packed: false },
	{ id: 2, title: "Watercolors", packed: false },
];

export default function TravelPlan() {
	const [items, setItems] = useState(initialItems);
	const [total, setTotal] = useState(3);
	const [packed, setPacked] = useState(1);

	function handleAddItem(title) {
		setTotal(total + 1);
		setItems([
			...items,
			{
				id: nextId++,
				title: title,
				packed: false,
			},
		]);
	}

	function handleChangeItem(nextItem) {
		if (nextItem.packed) {
			setPacked(packed + 1);
		} else {
			setPacked(packed - 1);
		}
		setItems(
			items.map((item) => {
				if (item.id === nextItem.id) {
					return nextItem;
				} else {
					return item;
				}
			})
		);
	}

	function handleDeleteItem(itemId) {
		setTotal(total - 1);
		setItems(items.filter((item) => item.id !== itemId));
	}

	return (
		<>
			<AddItem onAddItem={handleAddItem} />
			<PackingList
				items={items}
				onChangeItem={handleChangeItem}
				onDeleteItem={handleDeleteItem}
			/>
			<hr />
			<b>
				{packed} out of {total} packed!
			</b>
		</>
	);
}
```

```js
import { useState } from "react";

export default function AddItem({ onAddItem }) {
	const [title, setTitle] = useState("");
	return (
		<>
			<input
				placeholder="Add item"
				value={title}
				onChange={(e) => setTitle(e.target.value)}
			/>
			<button
				on_click={() => {
					setTitle("");
					onAddItem(title);
				}}
			>
				Add
			</button>
		</>
	);
}
```

```js
import { useState } from "react";

export default function PackingList({ items, onChangeItem, onDeleteItem }) {
	return (
		<ul>
			{items.map((item) => (
				<li key={item.id}>
					<label>
						<input
							type="checkbox"
							checked={item.packed}
							onChange={(e) => {
								onChangeItem({
									...item,
									packed: e.target.checked,
								});
							}}
						/>{" "}
						{item.title}
					</label>
					<button on_click={() => onDeleteItem(item.id)}>
						Delete
					</button>
				</li>
			))}
		</ul>
	);
}
```

```css
button {
	margin: 5px;
}
li {
	list-style-type: none;
}
ul,
li {
	margin: 0;
	padding: 0;
}
```

<Solution>

Although you could carefully change each event handler to update the `total` and `packed` counters correctly, the root problem is that these state variables exist at all. They are redundant because you can always calculate the number of items (packed or total) from the `items` array itself. Remove the redundant state to fix the bug:

```js
import { useState } from "react";
import AddItem from "./AddItem.js";
import PackingList from "./PackingList.js";

let nextId = 3;
const initialItems = [
	{ id: 0, title: "Warm socks", packed: true },
	{ id: 1, title: "Travel journal", packed: false },
	{ id: 2, title: "Watercolors", packed: false },
];

export default function TravelPlan() {
	const [items, setItems] = useState(initialItems);

	const total = items.length;
	const packed = items.filter((item) => item.packed).length;

	function handleAddItem(title) {
		setItems([
			...items,
			{
				id: nextId++,
				title: title,
				packed: false,
			},
		]);
	}

	function handleChangeItem(nextItem) {
		setItems(
			items.map((item) => {
				if (item.id === nextItem.id) {
					return nextItem;
				} else {
					return item;
				}
			})
		);
	}

	function handleDeleteItem(itemId) {
		setItems(items.filter((item) => item.id !== itemId));
	}

	return (
		<>
			<AddItem onAddItem={handleAddItem} />
			<PackingList
				items={items}
				onChangeItem={handleChangeItem}
				onDeleteItem={handleDeleteItem}
			/>
			<hr />
			<b>
				{packed} out of {total} packed!
			</b>
		</>
	);
}
```

```js
import { useState } from "react";

export default function AddItem({ onAddItem }) {
	const [title, setTitle] = useState("");
	return (
		<>
			<input
				placeholder="Add item"
				value={title}
				onChange={(e) => setTitle(e.target.value)}
			/>
			<button
				on_click={() => {
					setTitle("");
					onAddItem(title);
				}}
			>
				Add
			</button>
		</>
	);
}
```

```js
import { useState } from "react";

export default function PackingList({ items, onChangeItem, onDeleteItem }) {
	return (
		<ul>
			{items.map((item) => (
				<li key={item.id}>
					<label>
						<input
							type="checkbox"
							checked={item.packed}
							onChange={(e) => {
								onChangeItem({
									...item,
									packed: e.target.checked,
								});
							}}
						/>{" "}
						{item.title}
					</label>
					<button on_click={() => onDeleteItem(item.id)}>
						Delete
					</button>
				</li>
			))}
		</ul>
	);
}
```

```css
button {
	margin: 5px;
}
li {
	list-style-type: none;
}
ul,
li {
	margin: 0;
	padding: 0;
}
```

Notice how the event handlers are only concerned with calling `setItems` after this change. The item counts are now calculated during the next render from `items`, so they are always up-to-date.

</Solution>

#### Fix the disappearing selection

There is a list of `letters` in state. When you hover or focus a particular letter, it gets highlighted. The currently highlighted letter is stored in the `highlightedLetter` state variable. You can "star" and "unstar" individual letters, which updates the `letters` array in state.

This code works, but there is a minor UI glitch. When you press "Star" or "Unstar", the highlighting disappears for a moment. However, it reappears as soon as you move your pointer or switch to another letter with keyboard. Why is this happening? Fix it so that the highlighting doesn't disappear after the button click.

```js
import { useState } from "react";
import { initialLetters } from "./data.js";
import Letter from "./Letter.js";

export default function MailClient() {
	const [letters, setLetters] = useState(initialLetters);
	const [highlightedLetter, setHighlightedLetter] = useState(null);

	function handleHover(letter) {
		setHighlightedLetter(letter);
	}

	function handleStar(starred) {
		setLetters(
			letters.map((letter) => {
				if (letter.id === starred.id) {
					return {
						...letter,
						isStarred: !letter.isStarred,
					};
				} else {
					return letter;
				}
			})
		);
	}

	return (
		<>
			<h2>Inbox</h2>
			<ul>
				{letters.map((letter) => (
					<Letter
						key={letter.id}
						letter={letter}
						isHighlighted={letter === highlightedLetter}
						onHover={handleHover}
						onToggleStar={handleStar}
					/>
				))}
			</ul>
		</>
	);
}
```

```js
export default function Letter({
	letter,
	isHighlighted,
	onHover,
	onToggleStar,
}) {
	return (
		<li
			className={isHighlighted ? "highlighted" : ""}
			onFocus={() => {
				onHover(letter);
			}}
			onPointerMove={() => {
				onHover(letter);
			}}
		>
			<button
				on_click={() => {
					onToggleStar(letter);
				}}
			>
				{letter.isStarred ? "Unstar" : "Star"}
			</button>
			{letter.subject}
		</li>
	);
}
```

```js
export const initialLetters = [
	{
		id: 0,
		subject: "Ready for adventure?",
		isStarred: true,
	},
	{
		id: 1,
		subject: "Time to check in!",
		isStarred: false,
	},
	{
		id: 2,
		subject: "Festival Begins in Just SEVEN Days!",
		isStarred: false,
	},
];
```

```css
button {
	margin: 5px;
}
li {
	border-radius: 5px;
}
.highlighted {
	background: #d2eaff;
}
```

<Solution>

The problem is that you're holding the letter object in `highlightedLetter`. But you're also holding the same information in the `letters` array. So your state has duplication! When you update the `letters` array after the button click, you create a new letter object which is different from `highlightedLetter`. This is why `highlightedLetter === letter` check becomes `false`, and the highlight disappears. It reappears the next time you call `setHighlightedLetter` when the pointer moves.

To fix the issue, remove the duplication from state. Instead of storing _the letter itself_ in two places, store the `highlightedId` instead. Then you can check `isHighlighted` for each letter with `letter.id === highlightedId`, which will work even if the `letter` object has changed since the last render.

```js
import { useState } from "react";
import { initialLetters } from "./data.js";
import Letter from "./Letter.js";

export default function MailClient() {
	const [letters, setLetters] = useState(initialLetters);
	const [highlightedId, setHighlightedId] = useState(null);

	function handleHover(letterId) {
		setHighlightedId(letterId);
	}

	function handleStar(starredId) {
		setLetters(
			letters.map((letter) => {
				if (letter.id === starredId) {
					return {
						...letter,
						isStarred: !letter.isStarred,
					};
				} else {
					return letter;
				}
			})
		);
	}

	return (
		<>
			<h2>Inbox</h2>
			<ul>
				{letters.map((letter) => (
					<Letter
						key={letter.id}
						letter={letter}
						isHighlighted={letter.id === highlightedId}
						onHover={handleHover}
						onToggleStar={handleStar}
					/>
				))}
			</ul>
		</>
	);
}
```

```js
export default function Letter({
	letter,
	isHighlighted,
	onHover,
	onToggleStar,
}) {
	return (
		<li
			className={isHighlighted ? "highlighted" : ""}
			onFocus={() => {
				onHover(letter.id);
			}}
			onPointerMove={() => {
				onHover(letter.id);
			}}
		>
			<button
				on_click={() => {
					onToggleStar(letter.id);
				}}
			>
				{letter.isStarred ? "Unstar" : "Star"}
			</button>
			{letter.subject}
		</li>
	);
}
```

```js
export const initialLetters = [
	{
		id: 0,
		subject: "Ready for adventure?",
		isStarred: true,
	},
	{
		id: 1,
		subject: "Time to check in!",
		isStarred: false,
	},
	{
		id: 2,
		subject: "Festival Begins in Just SEVEN Days!",
		isStarred: false,
	},
];
```

```css
button {
	margin: 5px;
}
li {
	border-radius: 5px;
}
.highlighted {
	background: #d2eaff;
}
```

</Solution>

#### Implement multiple selection

In this example, each `Letter` has an `isSelected` prop and an `onToggle` handler that marks it as selected. This works, but the state is stored as a `selectedId` (either `null` or an ID), so only one letter can get selected at any given time.

Change the state structure to support multiple selection. (How would you structure it? Think about this before writing the code.) Each checkbox should become independent from the others. Clicking a selected letter should uncheck it. Finally, the footer should show the correct number of the selected items.

<Hint>

Instead of a single selected ID, you might want to hold an array or a [Set](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set) of selected IDs in state.

</Hint>

```js
import { useState } from "react";
import { letters } from "./data.js";
import Letter from "./Letter.js";

export default function MailClient() {
	const [selectedId, setSelectedId] = useState(null);

	// TODO: allow multiple selection
	const selectedCount = 1;

	function handleToggle(toggledId) {
		// TODO: allow multiple selection
		setSelectedId(toggledId);
	}

	return (
		<>
			<h2>Inbox</h2>
			<ul>
				{letters.map((letter) => (
					<Letter
						key={letter.id}
						letter={letter}
						isSelected={
							// TODO: allow multiple selection
							letter.id === selectedId
						}
						onToggle={handleToggle}
					/>
				))}
				<hr />
				<p>
					<b>You selected {selectedCount} letters</b>
				</p>
			</ul>
		</>
	);
}
```

```js
export default function Letter({ letter, onToggle, isSelected }) {
	return (
		<li className={isSelected ? "selected" : ""}>
			<label>
				<input
					type="checkbox"
					checked={isSelected}
					onChange={() => {
						onToggle(letter.id);
					}}
				/>
				{letter.subject}
			</label>
		</li>
	);
}
```

```js
export const letters = [
	{
		id: 0,
		subject: "Ready for adventure?",
		isStarred: true,
	},
	{
		id: 1,
		subject: "Time to check in!",
		isStarred: false,
	},
	{
		id: 2,
		subject: "Festival Begins in Just SEVEN Days!",
		isStarred: false,
	},
];
```

```css
input {
	margin: 5px;
}
li {
	border-radius: 5px;
}
label {
	width: 100%;
	padding: 5px;
	display: inline-block;
}
.selected {
	background: #d2eaff;
}
```

<Solution>

Instead of a single `selectedId`, keep a `selectedIds` _array_ in state. For example, if you select the first and the last letter, it would contain `[0, 2]`. When nothing is selected, it would be an empty `[]` array:

```js
import { useState } from "react";
import { letters } from "./data.js";
import Letter from "./Letter.js";

export default function MailClient() {
	const [selectedIds, setSelectedIds] = useState([]);

	const selectedCount = selectedIds.length;

	function handleToggle(toggledId) {
		// Was it previously selected?
		if (selectedIds.includes(toggledId)) {
			// Then remove this ID from the array.
			setSelectedIds(selectedIds.filter((id) => id !== toggledId));
		} else {
			// Otherwise, add this ID to the array.
			setSelectedIds([...selectedIds, toggledId]);
		}
	}

	return (
		<>
			<h2>Inbox</h2>
			<ul>
				{letters.map((letter) => (
					<Letter
						key={letter.id}
						letter={letter}
						isSelected={selectedIds.includes(letter.id)}
						onToggle={handleToggle}
					/>
				))}
				<hr />
				<p>
					<b>You selected {selectedCount} letters</b>
				</p>
			</ul>
		</>
	);
}
```

```js
export default function Letter({ letter, onToggle, isSelected }) {
	return (
		<li className={isSelected ? "selected" : ""}>
			<label>
				<input
					type="checkbox"
					checked={isSelected}
					onChange={() => {
						onToggle(letter.id);
					}}
				/>
				{letter.subject}
			</label>
		</li>
	);
}
```

```js
export const letters = [
	{
		id: 0,
		subject: "Ready for adventure?",
		isStarred: true,
	},
	{
		id: 1,
		subject: "Time to check in!",
		isStarred: false,
	},
	{
		id: 2,
		subject: "Festival Begins in Just SEVEN Days!",
		isStarred: false,
	},
];
```

```css
input {
	margin: 5px;
}
li {
	border-radius: 5px;
}
label {
	width: 100%;
	padding: 5px;
	display: inline-block;
}
.selected {
	background: #d2eaff;
}
```

One minor downside of using an array is that for each item, you're calling `selectedIds.includes(letter.id)` to check whether it's selected. If the array is very large, this can become a performance problem because array search with [`includes()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/includes) takes linear time, and you're doing this search for each individual item.

To fix this, you can hold a [Set](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set) in state instead, which provides a fast [`has()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set/has) operation:

```js
import { useState } from "react";
import { letters } from "./data.js";
import Letter from "./Letter.js";

export default function MailClient() {
	const [selectedIds, setSelectedIds] = useState(new Set());

	const selectedCount = selectedIds.size;

	function handleToggle(toggledId) {
		// Create a copy (to avoid mutation).
		const nextIds = new Set(selectedIds);
		if (nextIds.has(toggledId)) {
			nextIds.delete(toggledId);
		} else {
			nextIds.add(toggledId);
		}
		setSelectedIds(nextIds);
	}

	return (
		<>
			<h2>Inbox</h2>
			<ul>
				{letters.map((letter) => (
					<Letter
						key={letter.id}
						letter={letter}
						isSelected={selectedIds.has(letter.id)}
						onToggle={handleToggle}
					/>
				))}
				<hr />
				<p>
					<b>You selected {selectedCount} letters</b>
				</p>
			</ul>
		</>
	);
}
```

```js
export default function Letter({ letter, onToggle, isSelected }) {
	return (
		<li className={isSelected ? "selected" : ""}>
			<label>
				<input
					type="checkbox"
					checked={isSelected}
					onChange={() => {
						onToggle(letter.id);
					}}
				/>
				{letter.subject}
			</label>
		</li>
	);
}
```

```js
export const letters = [
	{
		id: 0,
		subject: "Ready for adventure?",
		isStarred: true,
	},
	{
		id: 1,
		subject: "Time to check in!",
		isStarred: false,
	},
	{
		id: 2,
		subject: "Festival Begins in Just SEVEN Days!",
		isStarred: false,
	},
];
```

```css
input {
	margin: 5px;
}
li {
	border-radius: 5px;
}
label {
	width: 100%;
	padding: 5px;
	display: inline-block;
}
.selected {
	background: #d2eaff;
}
```

Now each item does a `selectedIds.has(letter.id)` check, which is very fast.

Keep in mind that you [should not mutate objects in state](/learn/updating-objects-in-state), and that includes Sets, too. This is why the `handleToggle` function creates a _copy_ of the Set first, and then updates that copy.

</Solution>

</Challenges>
