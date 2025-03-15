## Overview

<p class="intro" markdown>

React can change how you think about the designs you look at and the apps you build. When you build a user interface with React, you will first break it apart into pieces called _components_. Then, you will describe the different visual states for each of your components. Finally, you will connect your components together so that the data flows through them. In this tutorial, we’ll guide you through the thought process of building a searchable product data table with React.

</p>

## Start with the mockup

Imagine that you already have a JSON API and a mockup from a designer.

The JSON API returns some data that looks like this:

```json linenums="0"
{% include "../../examples/thinking_in_react/start_with_the_mockup.json" %}
```

The mockup looks like this:

<img src="../../assets/images/s_thinking-in-react_ui.png" width="300" style="margin: 0 auto" />

To implement a UI in React, you will usually follow the same five steps.

## Step 1: Break the UI into a component hierarchy

Start by drawing boxes around every component and subcomponent in the mockup and naming them. If you work with a designer, they may have already named these components in their design tool. Ask them!

Depending on your background, you can think about splitting up a design into components in different ways:

-   **Programming**--use the same techniques for deciding if you should create a new function or object. One such technique is the [single responsibility principle](https://en.wikipedia.org/wiki/Single_responsibility_principle), that is, a component should ideally only do one thing. If it ends up growing, it should be decomposed into smaller subcomponents.
-   **CSS**--consider what you would make class selectors for. (However, components are a bit less granular.)
-   **Design**--consider how you would organize the design's layers.

If your JSON is well-structured, you'll often find that it naturally maps to the component structure of your UI. That's because UI and data models often have the same information architecture--that is, the same shape. Separate your UI into components, where each component matches one piece of your data model.

There are five components on this screen:

<!-- TODO: Change this image to use snake_case -->

<img src="../../assets/images/s_thinking-in-react_ui_outline.png" width="500" style="margin: 0 auto" />

1. `filterable_product_table` (grey) contains the entire app.
2. `search_bar` (blue) receives the user input.
3. `product_table` (lavender) displays and filters the list according to the user input.
4. `product_category_row` (green) displays a heading for each category.
5. `product_row` (yellow) displays a row for each product.

If you look at `product_table` (lavender), you'll see that the table header (containing the "Name" and "Price" labels) isn't its own component. This is a matter of preference, and you could go either way. For this example, it is a part of `product_table` because it appears inside the `product_table`'s list. However, if this header grows to be complex (e.g., if you add sorting), you can move it into its own `product_table_header` component.

Now that you've identified the components in the mockup, arrange them into a hierarchy. Components that appear within another component in the mockup should appear as a child in the hierarchy:

-   `filterable_product_table`
    -   `search_bar`
    -   `product_table`
        -   `product_category_row`
        -   `product_row`

## Step 2: Build a static version in React

Now that you have your component hierarchy, it's time to implement your app. The most straightforward approach is to build a version that renders the UI from your data model without adding any interactivity... yet! It's often easier to build the static version first and add interactivity later. Building a static version requires a lot of typing and no thinking, but adding interactivity requires a lot of thinking and not a lot of typing.

To build a static version of your app that renders your data model, you'll want to build [components](your-first-component.md) that reuse other components and pass data using [props.](../learn/passing-props-to-a-component.md) Props are a way of passing data from parent to child. (If you're familiar with the concept of [state](../learn/state-a-components-memory.md), don't use state at all to build this static version. State is reserved only for interactivity, that is, data that changes over time. Since this is a static version of the app, you don't need it.)

You can either build "top down" by starting with building the components higher up in the hierarchy (like `filterable_product_table`) or "bottom up" by working from components lower down (like `product_row`). In simpler examples, it’s usually easier to go top-down, and on larger projects, it’s easier to go bottom-up.

=== "app.py"

    ```python
    {% include "../../examples/thinking_in_react/build_a_static_version_in_react.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/thinking_in_react/build_a_static_version_in_react.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

(If this code looks intimidating, go through the [Quick Start](../learn/quick-start.md) first!)

After building your components, you'll have a library of reusable components that render your data model. Because this is a static app, the components will only return non-interactive HTML. The component at the top of the hierarchy (`filterable_product_table`) will take your data model as a prop. This is called _one-way data flow_ because the data flows down from the top-level component to the ones at the bottom of the tree.

!!! warning "Pitfall"

    At this point, you should not be using any state values. That’s for the next step!

## Step 3: Find the minimal but complete representation of UI state

To make the UI interactive, you need to let users change your underlying data model. You will use _state_ for this.

Think of state as the minimal set of changing data that your app needs to remember. The most important principle for structuring state is to keep it [DRY (Don't Repeat Yourself).](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) Figure out the absolute minimal representation of the state your application needs and compute everything else on-demand. For example, if you're building a shopping list, you can store the items as an array in state. If you want to also display the number of items in the list, don't store the number of items as another state value--instead, read the length of your array.

Now think of all of the pieces of data in this example application:

1. The original list of products
2. The search text the user has entered
3. The value of the checkbox
4. The filtered list of products

Which of these are state? Identify the ones that are not:

-   Does it **remain unchanged** over time? If so, it isn't state.
-   Is it **passed in from a parent** via props? If so, it isn't state.
-   **Can you compute it** based on existing state or props in your component? If so, it _definitely_ isn't state!

What's left is probably state.

Let's go through them one by one again:

1. The original list of products is **passed in as props, so it's not state.**
2. The search text seems to be state since it changes over time and can't be computed from anything.
3. The value of the checkbox seems to be state since it changes over time and can't be computed from anything.
4. The filtered list of products **isn't state because it can be computed** by taking the original list of products and filtering it according to the search text and value of the checkbox.

This means only the search text and the value of the checkbox are state! Nicely done!

!!! info "Deep Dive"

    <font size="4">**Props vs State**</font>

    There are two types of "model" data in React: props and state. The two are very different:

    -   [**Props** are like arguments you pass](../learn/passing-props-to-a-component.md) to a function. They let a parent component pass data to a child component and customize its appearance. For example, a `html.form` can pass a `color` prop to a `html.button`.
    -   [**State** is like a component’s memory.](../learn/state-a-components-memory.md) It lets a component keep track of some information and change it in response to interactions. For example, a `html.button` might keep track of `is_hovered` state.

    Props and state are different, but they work together. A parent component will often keep some information in state (so that it can change it), and _pass it down_ to child components as their props. It's okay if the difference still feels fuzzy on the first read. It takes a bit of practice for it to really stick!

## Step 4: Identify where your state should live

After identifying your app’s minimal state data, you need to identify which component is responsible for changing this state, or _owns_ the state. Remember: React uses one-way data flow, passing data down the component hierarchy from parent to child component. It may not be immediately clear which component should own what state. This can be challenging if you’re new to this concept, but you can figure it out by following these steps!

For each piece of state in your application:

1. Identify _every_ component that renders something based on that state.
2. Find their closest common parent component—a component above them all in the hierarchy.
3. Decide where the state should live:
    1. Often, you can put the state directly into their common parent.
    2. You can also put the state into some component above their common parent.
    3. If you can't find a component where it makes sense to own the state, create a new component solely for holding the state and add it somewhere in the hierarchy above the common parent component.

In the previous step, you found two pieces of state in this application: the search input text, and the value of the checkbox. In this example, they always appear together, so it makes sense to put them into the same place.

Now let's run through our strategy for them:

1. **Identify components that use state:**
    - `product_table` needs to filter the product list based on that state (search text and checkbox value).
    - `search_bar` needs to display that state (search text and checkbox value).
1. **Find their common parent:** The first parent component both components share is `filterable_product_table`.
1. **Decide where the state lives**: We'll keep the filter text and checked state values in `filterable_product_table`.

So the state values will live in `filterable_product_table`.

Add state to the component with the [`use_state()` Hook.](../reference/use-state.md) Hooks are special functions that let you "hook into" React. Add two state variables at the top of `filterable_product_table` and specify their initial state:

```python linenums="0"
{% include "../../examples/thinking_in_react/use_state.py" start="# start" %}
```

Then, pass `filter_text` and `in_stock_only` to `product_table` and `search_bar` as props:

```python linenums="0"
{% include "../../examples/thinking_in_react/use_state_with_components.py" start="# start" %}
```

You can start seeing how your application will behave. Edit the `filter_text` initial value from `use_state('')` to `use_state('fruit')` in the sandbox code below. You'll see both the search input text and the table update:

=== "app.py"

    ```python
    {% include "../../examples/thinking_in_react/identify_where_your_state_should_live.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/thinking_in_react/identify_where_your_state_should_live.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Notice that editing the form doesn't work yet.

In the code above, `product_table` and `search_bar` read the `filter_text` and `in_stock_only` props to render the table, the input, and the checkbox. For example, here is how `search_bar` populates the input value:

```python linenums="0" hl_lines="2 7"
{% include "../../examples/thinking_in_react/error_example.py" start="# start" %}
```

However, you haven't added any code to respond to the user actions like typing yet. This will be your final step.

## Step 5: Add inverse data flow

Currently your app renders correctly with props and state flowing down the hierarchy. But to change the state according to user input, you will need to support data flowing the other way: the form components deep in the hierarchy need to update the state in `filterable_product_table`.

React makes this data flow explicit, but it requires a little more typing than two-way data binding. If you try to type or check the box in the example above, you'll see that React ignores your input. This is intentional. By writing `<input value={filter_text} />`, you've set the `value` prop of the `input` to always be equal to the `filter_text` state passed in from `filterable_product_table`. Since `filter_text` state is never set, the input never changes.

You want to make it so whenever the user changes the form inputs, the state updates to reflect those changes. The state is owned by `filterable_product_table`, so only it can call `set_filter_text` and `set_in_stock_only`. To let `search_bar` update the `filterable_product_table`'s state, you need to pass these functions down to `search_bar`:

```python linenums="0" hl_lines="3-4 10-11"
{% include "../../examples/thinking_in_react/set_state_props.py" start="# start" %}
```

Inside the `search_bar`, you will add the `onChange` event handlers and set the parent state from them:

```python linenums="0" hl_lines="6"
{% include "../../examples/thinking_in_react/event_handlers.py" start="# start" %}
```

Now the application fully works!

=== "app.py"

    <!-- FIXME: Click event on the checkbox is broken. `event["target"]["checked"]` doesn't exist -->

    ```python
    {% include "../../examples/thinking_in_react/add_inverse_data_flow.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/thinking_in_react/add_inverse_data_flow.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

You can learn all about handling events and updating state in the [Adding Interactivity](../learn/responding-to-events.md) section.

## Where to go from here

This was a very brief introduction to how to think about building components and applications with React. You can [start a React project](../learn/start-a-new-react-project.md) right now or [dive deeper on all the syntax](../learn/your-first-component.md) used in this tutorial.
