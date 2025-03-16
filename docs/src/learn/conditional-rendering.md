## Overview

<p class="intro" markdown>

Your components will often need to display different things depending on different conditions. In React, you can conditionally render JSX using JavaScript syntax like `if` statements, `&&`, and `? :` operators.

</p>

!!! summary "You will learn"

    -   How to return different JSX depending on a condition
    -   How to conditionally include or exclude a piece of JSX
    -   Common conditional syntax shortcuts you’ll encounter in React codebases

## Conditionally returning JSX

Let’s say you have a `PackingList` component rendering several `Item`s, which can be marked as packed or not:

```js
function Item({ name, isPacked }) {
	return <li className="item">{name}</li>;
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

Notice that some of the `Item` components have their `isPacked` prop set to `true` instead of `false`. You want to add a checkmark (✔) to packed items if `isPacked={true}`.

You can write this as an [`if`/`else` statement](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/if...else) like so:

```js
if (isPacked) {
	return <li className="item">{name} ✔</li>;
}
return <li className="item">{name}</li>;
```

If the `isPacked` prop is `true`, this code **returns a different JSX tree.** With this change, some of the items get a checkmark at the end:

```js
function Item({ name, isPacked }) {
	if (isPacked) {
		return <li className="item">{name} ✔</li>;
	}
	return <li className="item">{name}</li>;
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

Try editing what gets returned in either case, and see how the result changes!

Notice how you're creating branching logic with JavaScript's `if` and `return` statements. In React, control flow (like conditions) is handled by JavaScript.

### Conditionally returning nothing with `null`

In some situations, you won't want to render anything at all. For example, say you don't want to show packed items at all. A component must return something. In this case, you can return `null`:

```js
if (isPacked) {
	return null;
}
return <li className="item">{name}</li>;
```

If `isPacked` is true, the component will return nothing, `null`. Otherwise, it will return JSX to render.

```js
function Item({ name, isPacked }) {
	if (isPacked) {
		return null;
	}
	return <li className="item">{name}</li>;
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

In practice, returning `null` from a component isn't common because it might surprise a developer trying to render it. More often, you would conditionally include or exclude the component in the parent component's JSX. Here's how to do that!

## Conditionally including JSX

In the previous example, you controlled which (if any!) JSX tree would be returned by the component. You may already have noticed some duplication in the render output:

```js
<li className="item">{name} ✔</li>
```

is very similar to

```js
<li className="item">{name}</li>
```

Both of the conditional branches return `<li className="item">...</li>`:

```js
if (isPacked) {
	return <li className="item">{name} ✔</li>;
}
return <li className="item">{name}</li>;
```

While this duplication isn't harmful, it could make your code harder to maintain. What if you want to change the `className`? You'd have to do it in two places in your code! In such a situation, you could conditionally include a little JSX to make your code more [DRY.](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)

### Conditional (ternary) operator (`? :`)

JavaScript has a compact syntax for writing a conditional expression -- the [conditional operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Conditional_Operator) or "ternary operator".

Instead of this:

```js
if (isPacked) {
	return <li className="item">{name} ✔</li>;
}
return <li className="item">{name}</li>;
```

You can write this:

```js
return <li className="item">{isPacked ? name + " ✔" : name}</li>;
```

You can read it as _"if `isPacked` is true, then (`?`) render `name + ' ✔'`, otherwise (`:`) render `name`"_.

<DeepDive>

#### Are these two examples fully equivalent?

If you're coming from an object-oriented programming background, you might assume that the two examples above are subtly different because one of them may create two different "instances" of `<li>`. But JSX elements aren't "instances" because they don't hold any internal state and aren't real DOM nodes. They're lightweight descriptions, like blueprints. So these two examples, in fact, _are_ completely equivalent. [Preserving and Resetting State](/learn/preserving-and-resetting-state) goes into detail about how this works.

</DeepDive>

Now let's say you want to wrap the completed item's text into another HTML tag, like `<del>` to strike it out. You can add even more newlines and parentheses so that it's easier to nest more JSX in each of the cases:

```js
function Item({ name, isPacked }) {
	return (
		<li className="item">{isPacked ? <del>{name + " ✔"}</del> : name}</li>
	);
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

This style works well for simple conditions, but use it in moderation. If your components get messy with too much nested conditional markup, consider extracting child components to clean things up. In React, markup is a part of your code, so you can use tools like variables and functions to tidy up complex expressions.

### Logical AND operator (`&&`)

Another common shortcut you'll encounter is the [JavaScript logical AND (`&&`) operator.](<https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Logical_AND#:~:text=The%20logical%20AND%20(%20%26%26%20)%20operator,it%20returns%20a%20Boolean%20value.>) Inside React components, it often comes up when you want to render some JSX when the condition is true, **or render nothing otherwise.** With `&&`, you could conditionally render the checkmark only if `isPacked` is `true`:

```js
return (
	<li className="item">
		{name} {isPacked && "✔"}
	</li>
);
```

You can read this as _"if `isPacked`, then (`&&`) render the checkmark, otherwise, render nothing"_.

Here it is in action:

```js
function Item({ name, isPacked }) {
	return (
		<li className="item">
			{name} {isPacked && "✔"}
		</li>
	);
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

A [JavaScript && expression](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Logical_AND) returns the value of its right side (in our case, the checkmark) if the left side (our condition) is `true`. But if the condition is `false`, the whole expression becomes `false`. React considers `false` as a "hole" in the JSX tree, just like `null` or `undefined`, and doesn't render anything in its place.

<Pitfall>

**Don't put numbers on the left side of `&&`.**

To test the condition, JavaScript converts the left side to a boolean automatically. However, if the left side is `0`, then the whole expression gets that value (`0`), and React will happily render `0` rather than nothing.

For example, a common mistake is to write code like `messageCount && <p>New messages</p>`. It's easy to assume that it renders nothing when `messageCount` is `0`, but it really renders the `0` itself!

To fix it, make the left side a boolean: `messageCount > 0 && <p>New messages</p>`.

</Pitfall>

### Conditionally assigning JSX to a variable

When the shortcuts get in the way of writing plain code, try using an `if` statement and a variable. You can reassign variables defined with [`let`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let), so start by providing the default content you want to display, the name:

```js
let itemContent = name;
```

Use an `if` statement to reassign a JSX expression to `itemContent` if `isPacked` is `true`:

```js
if (isPacked) {
	itemContent = name + " ✔";
}
```

[Curly braces open the "window into JavaScript".](/learn/javascript-in-jsx-with-curly-braces#using-curly-braces-a-window-into-the-javascript-world) Embed the variable with curly braces in the returned JSX tree, nesting the previously calculated expression inside of JSX:

```js
<li className="item">{itemContent}</li>
```

This style is the most verbose, but it's also the most flexible. Here it is in action:

```js
function Item({ name, isPacked }) {
	let itemContent = name;
	if (isPacked) {
		itemContent = name + " ✔";
	}
	return <li className="item">{itemContent}</li>;
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

Like before, this works not only for text, but for arbitrary JSX too:

```js
function Item({ name, isPacked }) {
	let itemContent = name;
	if (isPacked) {
		itemContent = <del>{name + " ✔"}</del>;
	}
	return <li className="item">{itemContent}</li>;
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

If you're not familiar with JavaScript, this variety of styles might seem overwhelming at first. However, learning them will help you read and write any JavaScript code -- and not just React components! Pick the one you prefer for a start, and then consult this reference again if you forget how the other ones work.

<Recap>

-   In React, you control branching logic with JavaScript.
-   You can return a JSX expression conditionally with an `if` statement.
-   You can conditionally save some JSX to a variable and then include it inside other JSX by using the curly braces.
-   In JSX, `{cond ? <A /> : <B />}` means _"if `cond`, render `<A />`, otherwise `<B />`"_.
-   In JSX, `{cond && <A />}` means _"if `cond`, render `<A />`, otherwise nothing"_.
-   The shortcuts are common, but you don't have to use them if you prefer plain `if`.

</Recap>

<Challenges>

#### Show an icon for incomplete items with `? :`

Use the conditional operator (`cond ? a : b`) to render a ❌ if `isPacked` isn’t `true`.

```js
function Item({ name, isPacked }) {
	return (
		<li className="item">
			{name} {isPacked && "✔"}
		</li>
	);
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

<Solution>

```js
function Item({ name, isPacked }) {
	return (
		<li className="item">
			{name} {isPacked ? "✔" : "❌"}
		</li>
	);
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item isPacked={true} name="Space suit" />
				<Item isPacked={true} name="Helmet with a golden leaf" />
				<Item isPacked={false} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

</Solution>

#### Show the item importance with `&&`

In this example, each `Item` receives a numerical `importance` prop. Use the `&&` operator to render "_(Importance: X)_" in italics, but only for items that have non-zero importance. Your item list should end up looking like this:

-   Space suit _(Importance: 9)_
-   Helmet with a golden leaf
-   Photo of Tam _(Importance: 6)_

Don't forget to add a space between the two labels!

```js
function Item({ name, importance }) {
	return <li className="item">{name}</li>;
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item importance={9} name="Space suit" />
				<Item importance={0} name="Helmet with a golden leaf" />
				<Item importance={6} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

<Solution>

This should do the trick:

```js
function Item({ name, importance }) {
	return (
		<li className="item">
			{name}
			{importance > 0 && " "}
			{importance > 0 && <i>(Importance: {importance})</i>}
		</li>
	);
}

export default function PackingList() {
	return (
		<section>
			<h1>Sally Ride's Packing List</h1>
			<ul>
				<Item importance={9} name="Space suit" />
				<Item importance={0} name="Helmet with a golden leaf" />
				<Item importance={6} name="Photo of Tam" />
			</ul>
		</section>
	);
}
```

Note that you must write `importance > 0 && ...` rather than `importance && ...` so that if the `importance` is `0`, `0` isn't rendered as the result!

In this solution, two separate conditions are used to insert a space between the name and the importance label. Alternatively, you could use a fragment with a leading space: `importance > 0 && <> <i>...</i></>` or add a space immediately inside the `<i>`: `importance > 0 && <i> ...</i>`.

</Solution>

#### Refactor a series of `? :` to `if` and variables

This `Drink` component uses a series of `? :` conditions to show different information depending on whether the `name` prop is `"tea"` or `"coffee"`. The problem is that the information about each drink is spread across multiple conditions. Refactor this code to use a single `if` statement instead of three `? :` conditions.

```js
function Drink({ name }) {
	return (
		<section>
			<h1>{name}</h1>
			<dl>
				<dt>Part of plant</dt>
				<dd>{name === "tea" ? "leaf" : "bean"}</dd>
				<dt>Caffeine content</dt>
				<dd>{name === "tea" ? "15–70 mg/cup" : "80–185 mg/cup"}</dd>
				<dt>Age</dt>
				<dd>{name === "tea" ? "4,000+ years" : "1,000+ years"}</dd>
			</dl>
		</section>
	);
}

export default function DrinkList() {
	return (
		<div>
			<Drink name="tea" />
			<Drink name="coffee" />
		</div>
	);
}
```

Once you've refactored the code to use `if`, do you have further ideas on how to simplify it?

<Solution>

There are multiple ways you could go about this, but here is one starting point:

```js
function Drink({ name }) {
	let part, caffeine, age;
	if (name === "tea") {
		part = "leaf";
		caffeine = "15–70 mg/cup";
		age = "4,000+ years";
	} else if (name === "coffee") {
		part = "bean";
		caffeine = "80–185 mg/cup";
		age = "1,000+ years";
	}
	return (
		<section>
			<h1>{name}</h1>
			<dl>
				<dt>Part of plant</dt>
				<dd>{part}</dd>
				<dt>Caffeine content</dt>
				<dd>{caffeine}</dd>
				<dt>Age</dt>
				<dd>{age}</dd>
			</dl>
		</section>
	);
}

export default function DrinkList() {
	return (
		<div>
			<Drink name="tea" />
			<Drink name="coffee" />
		</div>
	);
}
```

Here the information about each drink is grouped together instead of being spread across multiple conditions. This makes it easier to add more drinks in the future.

Another solution would be to remove the condition altogether by moving the information into objects:

```js
const drinks = {
	tea: {
		part: "leaf",
		caffeine: "15–70 mg/cup",
		age: "4,000+ years",
	},
	coffee: {
		part: "bean",
		caffeine: "80–185 mg/cup",
		age: "1,000+ years",
	},
};

function Drink({ name }) {
	const info = drinks[name];
	return (
		<section>
			<h1>{name}</h1>
			<dl>
				<dt>Part of plant</dt>
				<dd>{info.part}</dd>
				<dt>Caffeine content</dt>
				<dd>{info.caffeine}</dd>
				<dt>Age</dt>
				<dd>{info.age}</dd>
			</dl>
		</section>
	);
}

export default function DrinkList() {
	return (
		<div>
			<Drink name="tea" />
			<Drink name="coffee" />
		</div>
	);
}
```

</Solution>

</Challenges>
