!!! warning "Planned / Undeveloped"

    This feature is planned, but not yet developed.

    See [this issue](https://github.com/reactive-python/reactpy/issues/1072) for more details.

<!--
## Overview

<p class="intro" markdown>

Use React Developer Tools to inspect React [components](../learn/your-first-component.md), edit [props](../learn/passing-props-to-a-component.md) and [state](../learn/state-a-components-memory.md), and identify performance problems.

</p>

!!! summary "You will learn"

    -   How to install ReactPy Developer Tools


## Browser extension

The easiest way to debug websites built with React is to install the React Developer Tools browser extension. It is available for several popular browsers:

-   [Install for **Chrome**](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi?hl=en)
-   [Install for **Firefox**](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)
-   [Install for **Edge**](https://microsoftedge.microsoft.com/addons/detail/react-developer-tools/gpphkfbcpidddadnkolkpfckpihlkkil)

Now, if you visit a website **built with React,** you will see the _Components_ and _Profiler_ panels.

![React Developer Tools extension](/images/docs/react-devtools-extension.png)

### Safari and other browsers

For other browsers (for example, Safari), install the [`react-devtools`](https://www.npmjs.com/package/react-devtools) npm package:

```bash
# Yarn
yarn global add react-devtools

# Npm
npm install -g react-devtools
```

Next open the developer tools from the terminal:

```bash
react-devtools
```

Then connect your website by adding the following `<script>` tag to the beginning of your website's `<head>`:

```html
<html>
	<head>
		<script src="http://localhost:8097"></script>
	</head>
</html>
```

Reload your website in the browser now to view it in developer tools.

![React Developer Tools standalone](/images/docs/react-devtools-standalone.png)

## Mobile (React Native)

React Developer Tools can be used to inspect apps built with [React Native](https://reactnative.dev/) as well.

The easiest way to use React Developer Tools is to install it globally:

```bash
# Yarn
yarn global add react-devtools

# Npm
npm install -g react-devtools
```

Next open the developer tools from the terminal.

```bash
react-devtools
```

It should connect to any local React Native app that's running.

> Try reloading the app if developer tools doesn't connect after a few seconds.

[Learn more about debugging React Native.](https://reactnative.dev/docs/debugging) -->
