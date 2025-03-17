## Overview

<p class="intro" markdown>

A properly configured editor can make code clearer to read and faster to write. It can even help you catch bugs as you write them! If this is your first time setting up an editor or you're looking to tune up your current editor, we have a few recommendations.

</p>

!!! summary "You will learn"

    -   What the most popular editors are
    -   How to format your code automatically

## Your editor

[VS Code](https://code.visualstudio.com/) is one of the most popular editors in use today. It has a large marketplace of extensions and integrates well with popular services like GitHub. Most of the features listed below can be added to VS Code as extensions as well, making it highly configurable!

Other popular text editors used in the React community include:

-   [Sublime Text](https://www.sublimetext.com/) has support for [syntax highlighting](https://stackoverflow.com/a/70960574/458193) and autocomplete built in.
-   [Vim](https://www.vim.org/) is a highly configurable text editor built to make creating and changing any kind of text very efficient. It is included as "vi" with most UNIX systems and with Apple OS X.

## Recommended text editor features

Some editors come with these features built in, but others might require adding an extension. Check to see what support your editor of choice provides to be sure!

### Linting

Linting is the process of running a program that will analyse code for potential errors. [Ruff](https://docs.astral.sh/ruff/) is Reactive Python's linter of choice due to its speed and configurability. Additionally, we recommend using [Pyright](https://microsoft.github.io/pyright/) as a performant type checker for Python.

Be sure you have [Python installed](https://www.python.org/downloads/) before you proceed!

-   [Install Ruff using the VSCode extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) or the [standalone package](https://docs.astral.sh/ruff/installation/).
-   [Install Pyright using the VSCode extension](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) or the [standalone package](https://microsoft.github.io/pyright/#/installation).

### Formatting

The last thing you want to do when sharing your code with another contributor is get into an discussion about [tabs vs spaces](https://www.google.com/search?q=tabs+vs+spaces)! Fortunately, [Ruff](https://docs.astral.sh/ruff/) will clean up your code by reformatting it to conform to preset, configurable rules. Run Ruff, and all your tabs will be converted to spaces—and your indentation, quotes, etc will also all be changed to conform to the configuration. In the ideal setup, Ruff will run when you save your file, quickly making these edits for you.

You can install the [Ruff extension in VSCode](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) by following these steps:

1. Launch VS Code
2. Use Quick Open, press ++ctrl+p++
3. Paste in `ext install charliermarsh.ruff`
4. Press Enter

**Formatting on save**

Ideally, you should format your code on every save. VS Code has settings for this!

1. In VS Code, press ++ctrl+shift+p++
2. Type "workspace settings"
3. Hit Enter
4. In the search bar, type "Format on save"
5. Be sure the "Format on save" option is ticked!
