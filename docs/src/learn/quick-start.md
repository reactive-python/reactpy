## Overview

<p class="intro" markdown>

Welcome to the ReactPy documentation! This page will give you an introduction to the 80% of React concepts that you will use on a daily basis.

</p>

!!! summary "You will learn"

    -   How to create and nest components
    -   How to add markup and styles
    -   How to display data
    -   How to render conditions and lists
    -   How to respond to events and update the screen
    -   How to share data between components

## Creating and nesting components

React apps are made out of _components_. A component is a piece of the UI (user interface) that has its own logic and appearance. A component can be as small as a button, or as large as an entire page.

React components are Python functions that return markup:

```python linenums="0"
{% include "../../examples/quick_start/my_button.py" start="# start" %}
```

Now that you've declared `my_button`, you can nest it into another component:

```python linenums="0" hl_lines="5"
{% include "../../examples/quick_start/my_app.py" start="# start" %}
```

Have a look at the result:

=== "app.py"

    ```python
    {% include "../../examples/quick_start/creating_and_nesting_components.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

<!-- ## Writing markup with JSX

The markup syntax you've seen above is called _JSX_. It is optional, but most React projects use JSX for its convenience. All of the [tools we recommend for local development](/learn/installation) support JSX out of the box.

JSX is stricter than HTML. You have to close tags like `<br />`. Your component also can't return multiple JSX tags. You have to wrap them into a shared parent, like a `<div>...</div>` or an empty `<>...</>` wrapper:

```js
function AboutPage() {
	return (
		<>
			<h1>About</h1>
			<p>
				Hello there.
				<br />
				How do you do?
			</p>
		</>
	);
}
```

If you have a lot of HTML to port to JSX, you can use an [online converter.](https://transform.tools/html-to-jsx) -->

## Adding styles

In React, you specify a CSS class with `className`. It works the same way as the HTML [`class`](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/class) attribute:

```python linenums="0"
{% include "../../examples/quick_start/adding_styles.py" start="# start" %}
```

Then you write the CSS rules for it in a separate CSS file:

```css linenums="0"
{% include "../../examples/quick_start/adding_styles.css" %}
```

React does not prescribe how you add CSS files. In the simplest case, you'll add a [`<link>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/link) tag to your HTML. If you use a build tool or web framework, consult its documentation to learn how to add a CSS file to your project.

## Displaying data

<!-- JSX lets you put markup into JavaScript. Curly braces let you "escape back" into JavaScript so that you can embed some variable from your code and display it to the user. For example, this will display `user.name`:

```js
return <h1>{user.name}</h1>;
```

You can also "escape into JavaScript" from JSX attributes, but you have to use curly braces _instead of_ quotes. For example, `className="avatar"` passes the `"avatar"` string as the CSS class, but `src={user.imageUrl}` reads the JavaScript `user.imageUrl` variable value, and then passes that value as the `src` attribute:

```js
return <img className="avatar" src={user.imageUrl} />;
```

You can put more complex expressions inside the JSX curly braces too, for example, [string concatenation](https://javascript.info/operators#string-concatenation-with-binary): -->

You can fetch data from a variety of sources and directly embed it into your components. You can also use the `style` attribute when your styles depend on JavaScript variables.

=== "app.py"

    ```python
    {% include "../../examples/quick_start/displaying_data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/quick_start/displaying_data.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

## Conditional rendering

In React, there is no special syntax for writing conditions. Instead, you'll use the same techniques as you use when writing regular Python code. For example, you can use an `if` statement to conditionally include components:

```python linenums="0"
{% include "../../examples/quick_start/conditional_rendering.py" start="# start"%}
```

If you prefer more compact code, you can use the [ternary operator.](https://www.geeksforgeeks.org/ternary-operator-in-python/):

```python linenums="0"
{% include "../../examples/quick_start/conditional_rendering_ternary.py" start="# start"%}
```

When you don't need the `else` branch, you can also use a shorter [logical `and` syntax](https://www.geeksforgeeks.org/short-circuiting-techniques-python/):

```python linenums="0"
{% include "../../examples/quick_start/conditional_rendering_logical_and.py" start="# start" %}
```

All of these approaches also work for conditionally specifying attributes. If you're unfamiliar with some of this Python syntax, you can start by always using `if...else`.

## Rendering lists

You will rely on Python features like [`for` loop](https://www.w3schools.com/python/quick_start/python_for_loops.asp) and [list comprehension](https://www.w3schools.com/python/quick_start/python_lists_comprehension.asp) to render lists of components.

For example, let's say you have an array of products:

```python linenums="0"
{% include "../../examples/quick_start/rendering_lists_products.py" %}
```

Inside your component, use list comprehension to transform an array of products into an array of `#!html <li>` items:

```python linenums="0"
{% include "../../examples/quick_start/rendering_lists_list_items.py" start="# start" %}
```

Notice how `#!html <li>` has a `key` attribute. For each item in a list, you should pass a string or a number that uniquely identifies that item among its siblings. Usually, a key should be coming from your data, such as a database ID. React uses your keys to know what happened if you later insert, delete, or reorder the items.

=== "app.py"

    ```python
    {% include "../../examples/quick_start/rendering_lists.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

## Responding to events

You can respond to events by declaring _event handler_ functions inside your components:

```python linenums="0"  hl_lines="3-4 7"
{% include "../../examples/quick_start/responding_to_events.py" start="# start" %}
```

Notice how `"onClick": handle_click` has no parentheses at the end! Do not _call_ the event handler function: you only need to _pass it down_. React will call your event handler when the user clicks the button.

## Updating the screen

Often, you'll want your component to "remember" some information and display it. For example, maybe you want to count the number of times a button is clicked. To do this, add _state_ to your component.

First, import [`use_state`](../reference/use-state.md) from React:

```python linenums="0"
{% include "../../examples/quick_start/updating_the_screen_use_state.py" end="# end" %}
```

Now you can declare a _state variable_ inside your component:

```python linenums="0"
{% include "../../examples/quick_start/updating_the_screen_use_state_button.py" start="# start" %}
```

You’ll get two things from `use_state`: the current state (`count`), and the function that lets you update it (`set_count`). You can give them any names, but the convention is to write `something, set_something = ...`.

The first time the button is displayed, `count` will be `0` because you passed `0` to `use_state()`. When you want to change state, call `set_count()` and pass the new value to it. Clicking this button will increment the counter:

```python linenums="0" hl_lines="6"
{% include "../../examples/quick_start/updating_the_screen_event.py" start="# start" %}
```

React will call your component function again. This time, `count` will be `1`. Then it will be `2`. And so on.

If you render the same component multiple times, each will get its own state. Click each button separately:

=== "app.py"

    ```python
    {% include "../../examples/quick_start/updating_the_screen.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/quick_start/updating_the_screen.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Notice how each button "remembers" its own `count` state and doesn't affect other buttons.

## Using Hooks

Functions starting with `use` are called _Hooks_. `use_state` is a built-in Hook provided by React. You can find other built-in Hooks in the [API reference.](../reference/use-state.md) You can also write your own Hooks by combining the existing ones.

Hooks are more restrictive than other functions. You can only call Hooks _at the top_ of your components (or other Hooks). If you want to use `use_state` in a condition or a loop, extract a new component and put it there.

## Sharing data between components

In the previous example, each `my_button` had its own independent `count`, and when each button was clicked, only the `count` for the button clicked changed:

<!-- TODO: Diagram -->

However, often you'll need components to _share data and always update together_.

To make both `my_button` components display the same `count` and update together, you need to move the state from the individual buttons "upwards" to the closest component containing all of them.

In this example, it is `my_app`.

<!-- TODO: Diagram -->

Now when you click either button, the `count` in `my_app` will change, which will change both of the counts in `my_button`. Here's how you can express this in code.

First, _move the state up_ from `my_button` into `my_app`:

```python linenums="0" hl_lines="3-6 17"
{% include "../../examples/quick_start/sharing_data_between_components_move_state.py" start="# start" %}
```

Then, _pass the state down_ from `my_app` to each `my_button`, together with the shared click handler. You can pass information to `my_button` using props:

```python linenums="0" hl_lines="10-11"
{% include "../../examples/quick_start/sharing_data_between_components_props.py" start="# start" end="# end" %}
```

The information you pass down like this is called _props_. Now the `my_app` component contains the `count` state and the `handle_click` event handler, and _passes both of them down as props_ to each of the buttons.

Finally, change `my_button` to _read_ the props you have passed from its parent component:

```python linenums="0"
{% include "../../examples/quick_start/sharing_data_between_components_button.py" start="# start" %}
```

When you click the button, the `on_click` handler fires. Each button's `on_click` prop was set to the `handle_click` function inside `my_app`, so the code inside of it runs. That code calls `set_count(count + 1)`, incrementing the `count` state variable. The new `count` value is passed as a prop to each button, so they all show the new value. This is called "lifting state up". By moving state up, you've shared it between components.

=== "app.py"

    ```python
    {% include "../../examples/quick_start/sharing_data_between_components.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/quick_start/sharing_data_between_components.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

## Next Steps

By now, you know the basics of how to write React code!

Check out the [Tutorial](./tutorial-tic-tac-toe.md) to put them into practice and build your first mini-app with React.
