
!!! warning "In Progress"

    This feature is planned, but not yet developed.

    See [this issue](https://github.com/reactive-python/reactpy/issues/918) for more details.

## Overview

<p class="intro" markdown>

_PSX_ is a syntax extension for JavaScript that lets you write HTML-like markup inside a JavaScript file. Although there are other ways to write components, most React developers prefer the conciseness of PSX, and most codebases use it.

</p>

!!! summary "You Will Learn"

    -   Why React mixes markup with rendering logic
    -   How PSX is different from HTML
    -   How to display information with PSX

## PSX: Putting markup into Python

The Web has been built on HTML, CSS, and JavaScript. For many years, web developers kept content in HTML, design in CSS, and logic in JavaScript—often in separate files! Content was marked up inside HTML while the page's logic lived separately in JavaScript:

<!-- TODO: Diagram -->

But as the Web became more interactive, logic increasingly determined content. Scripting languages are now in charge of the HTML! This is why **in React, rendering logic and markup live together in the same place—components.**

<!-- TODO: Diagram -->

Keeping a button's rendering logic and markup together ensures that they stay in sync with each other on every edit. Conversely, details that are unrelated, such as the button's markup and a sidebar's markup, are isolated from each other, making it safer to change either of them on their own.

Each React component is a JavaScript function that may contain some markup that React renders into the browser. React components use a syntax extension called PSX to represent that markup. PSX looks a lot like HTML, but it is a bit stricter and can display dynamic information. The best way to understand this is to convert some HTML markup to PSX markup.

!!! note

    PSX and ReactPy are two separate things. They're often used together, but you _can_ use them independently of each other. PSX is a syntax extension, while ReactPy is a Python library.

<!-- ## Converting HTML to PSX

Suppose that you have some (perfectly valid) HTML:

```html
<h1>Hedy Lamarr's Todos</h1>
<img src="https://i.imgur.com/yXOvdOSs.jpg" alt="Hedy Lamarr" class="photo" />
<ul>
	<li>Invent new traffic lights</li>
	<li>Rehearse a movie scene</li>
	<li>Improve the spectrum technology</li>
</ul>
```

And you want to put it into your component:

```js
export default function TodoList() {
  return (
    // ???
  )
}
```

If you copy and paste it as is, it will not work:

```js
export default function TodoList() {
  return (
    // This doesn't quite work!
    <h1>Hedy Lamarr's Todos</h1>
    <img
      src="https://i.imgur.com/yXOvdOSs.jpg"
      alt="Hedy Lamarr"
      class="photo"
    >
    <ul>
      <li>Invent new traffic lights
      <li>Rehearse a movie scene
      <li>Improve the spectrum technology
    </ul>
  );
}
```

```css
img {
	height: 90px;
}
```

This is because PSX is stricter and has a few more rules than HTML! If you read the error messages above, they'll guide you to fix the markup, or you can follow the guide below.

<Note>

Most of the time, React's on-screen error messages will help you find where the problem is. Give them a read if you get stuck!

</Note>

## The Rules of PSX

### 1. Return a single root element

To return multiple elements from a component, **wrap them with a single parent tag.**

For example, you can use a `<div>`:

```js
<div>
  <h1>Hedy Lamarr's Todos</h1>
  <img
    src="https://i.imgur.com/yXOvdOSs.jpg"
    alt="Hedy Lamarr"
    class="photo"
  >
  <ul>
    ...
  </ul>
</div>
```

If you don't want to add an extra `<div>` to your markup, you can write `<>` and `</>` instead:

```js
<>
  <h1>Hedy Lamarr's Todos</h1>
  <img
    src="https://i.imgur.com/yXOvdOSs.jpg"
    alt="Hedy Lamarr"
    class="photo"
  >
  <ul>
    ...
  </ul>
</>
```

This empty tag is called a _[Fragment.](/reference/react/Fragment)_ Fragments let you group things without leaving any trace in the browser HTML tree.

<DeepDive>

#### Why do multiple PSX tags need to be wrapped?

PSX looks like HTML, but under the hood it is transformed into plain JavaScript objects. You can't return two objects from a function without wrapping them into an array. This explains why you also can't return two PSX tags without wrapping them into another tag or a Fragment.

</DeepDive>

### 2. Close all the tags

PSX requires tags to be explicitly closed: self-closing tags like `<img>` must become `<img />`, and wrapping tags like `<li>oranges` must be written as `<li>oranges</li>`.

This is how Hedy Lamarr's image and list items look closed:

```js
<>
	<img
		src="https://i.imgur.com/yXOvdOSs.jpg"
		alt="Hedy Lamarr"
		class="photo"
	/>
	<ul>
		<li>Invent new traffic lights</li>
		<li>Rehearse a movie scene</li>
		<li>Improve the spectrum technology</li>
	</ul>
</>
```

### 3. camelCase <s>all</s> most of the things!

PSX turns into JavaScript and attributes written in PSX become keys of JavaScript objects. In your own components, you will often want to read those attributes into variables. But JavaScript has limitations on variable names. For example, their names can't contain dashes or be reserved words like `class`.

This is why, in React, many HTML and SVG attributes are written in camelCase. For example, instead of `stroke-width` you use `strokeWidth`. Since `class` is a reserved word, in React you write `className` instead, named after the [corresponding DOM property](https://developer.mozilla.org/en-US/docs/Web/API/Element/className):

```js
<img
	src="https://i.imgur.com/yXOvdOSs.jpg"
	alt="Hedy Lamarr"
	className="photo"
/>
```

You can [find all these attributes in the list of DOM component props.](/reference/react-dom/components/common) If you get one wrong, don't worry—React will print a message with a possible correction to the [browser console.](https://developer.mozilla.org/docs/Tools/Browser_Console)

<Pitfall>

For historical reasons, [`aria-*`](https://developer.mozilla.org/docs/Web/Accessibility/ARIA) and [`data-*`](https://developer.mozilla.org/docs/Learn/HTML/Howto/Use_data_attributes) attributes are written as in HTML with dashes.

</Pitfall>

### Pro-tip: Use a PSX Converter

Converting all these attributes in existing markup can be tedious! We recommend using a [converter](https://transform.tools/html-to-psx) to translate your existing HTML and SVG to PSX. Converters are very useful in practice, but it's still worth understanding what is going on so that you can comfortably write PSX on your own.

Here is your final result:

```js
export default function TodoList() {
	return (
		<>
			<h1>Hedy Lamarr's Todos</h1>
			<img
				src="https://i.imgur.com/yXOvdOSs.jpg"
				alt="Hedy Lamarr"
				className="photo"
			/>
			<ul>
				<li>Invent new traffic lights</li>
				<li>Rehearse a movie scene</li>
				<li>Improve the spectrum technology</li>
			</ul>
		</>
	);
}
```

```css
img {
	height: 90px;
}
```

<Recap>

Now you know why PSX exists and how to use it in components:

-   React components group rendering logic together with markup because they are related.
-   PSX is similar to HTML, with a few differences. You can use a [converter](https://transform.tools/html-to-psx) if you need to.
-   Error messages will often point you in the right direction to fixing your markup.

</Recap>

<Challenges>

#### Convert some HTML to PSX

This HTML was pasted into a component, but it's not valid PSX. Fix it:

```js
export default function Bio() {
  return (
    <div class="intro">
      <h1>Welcome to my website!</h1>
    </div>
    <p class="summary">
      You can find my thoughts here.
      <br><br>
      <b>And <i>pictures</b></i> of scientists!
    </p>
  );
}
```

```css
.intro {
	background-image: linear-gradient(
		to left,
		violet,
		indigo,
		blue,
		green,
		yellow,
		orange,
		red
	);
	background-clip: text;
	color: transparent;
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
}

.summary {
	padding: 20px;
	border: 10px solid gold;
}
```

Whether to do it by hand or using the converter is up to you!

<Solution>

```js
export default function Bio() {
	return (
		<div>
			<div className="intro">
				<h1>Welcome to my website!</h1>
			</div>
			<p className="summary">
				You can find my thoughts here.
				<br />
				<br />
				<b>
					And <i>pictures</i>
				</b> of scientists!
			</p>
		</div>
	);
}
```

```css
.intro {
	background-image: linear-gradient(
		to left,
		violet,
		indigo,
		blue,
		green,
		yellow,
		orange,
		red
	);
	background-clip: text;
	color: transparent;
	-webkit-background-clip: text;
	-webkit-text-fill-color: transparent;
}

.summary {
	padding: 20px;
	border: 10px solid gold;
}
```

</Solution>

</Challenges> -->
