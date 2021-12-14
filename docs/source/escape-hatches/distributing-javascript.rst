Distributing Javascript
=======================

There are two ways that you can distribute your :ref:`Custom Javascript Components`:

- Using a CDN_
- In a Python package via PyPI_

These options are not mutually exclusive though, and it may be beneficial to support
both options. For example, if you upload your Javascript components to NPM_ and also
bundle your Javascript inside a Python package, in principle your users can determine
which work best for them. Regardless though, either you or, if you give then the choice,
your users, will have to consider the tradeoffs of either approach.

- :ref:`Distributing Javascript via CDN_` - Most useful in production-grade applications
  where its assumed the user has a network connection. In this scenario a CDN's `edge
  network <https://en.wikipedia.org/wiki/Edge_computing>`__ can be used to bring the
  Javascript source closer to the user in order to reduce page load times.

- :ref:`Distributing Javascript via PyPI_` - This method is ideal for local usage since
  the user can server all the Javascript components they depend on from their computer
  without requiring a network connection.


Distributing Javascript via CDN_
--------------------------------

Under this approach, to simplify these instructions, we're going to ignore the problem
of distributing the Javascript since that must be handled by your CDN. For open source
or personal projects, a CDN like https://unpkg.com/ makes things easy by automatically
preparing any package that's been uploaded to NPM_. If you need to roll with your own
private CDN, this will likely be more complicated.

In either case though, on the Python side, things are quite simple. You need only pass
the URL where your package can be found to :func:`~idom.web.module.module_from_url`
where you can then load any of its exports:

.. code-block::

    import idom

    your_module = ido.web.module_from_url("https://some.cdn/your-module")
    YourComponent = idom.web.export(your_module, "YourComponent")


Distributing Javascript via PyPI_
---------------------------------

This can be most easily accomplished by using the `template repository`_ that's been
purpose-built for this. However, to get a better sense for its inner workings, we'll
briefly look at what's required. At a high level, we must consider how to...

1. bundle your Javascript into an `ECMAScript Module`)
2. include that Javascript bundle in a Python package
3. use it as a component in your application using IDOM

In the descriptions to follow we'll be assuming that:

- NPM_ is the Javascript package manager
- The components are implemented with React_
- Rollup_ bundles the Javascript module
- Setuptools_ builds the Python package

To start, let's take a look at the file structure we'll be building:

.. code-block:: text

    your-project
    |-- js
    |   |-- src
    |   |   \-- index.js
    |   |-- package.json
    |   \-- rollup.config.js
    |-- your_python_package
    |   |-- __init__.py
    |   \-- widget.py
    |-- Manifest.in
    |-- pyproject.toml
    \-- setup.py

``index.js`` should contain the relevant exports (see
:ref:`Custom JavaScript Components` for more info):

.. code-block:: javascript

    import * as React from "react";
    import * as ReactDOM from "react-dom";

    export function bind(node, config) {
        return {
            create: (component, props, children) =>
                React.createElement(component, props, ...children),
            render: (element) => ReactDOM.render(element, node),
            unmount: () => ReactDOM.unmountComponentAtNode(node),
        };
    }

    // exports for your components
    export YourFirstComponent(props) {...};
    export YourSecondComponent(props) {...};
    export YourThirdComponent(props) {...};


Your ``package.json`` should include the following:

.. code-block:: python

    {
      "name": "YOUR-PACKAGE-NAME",
      "scripts": {
        "build": "rollup --config",
        ...
      },
      "devDependencies": {
        "rollup": "^2.35.1",
        "rollup-plugin-commonjs": "^10.1.0",
        "rollup-plugin-node-resolve": "^5.2.0",
        "rollup-plugin-replace": "^2.2.0",
        ...
      },
      "dependencies": {
        "react": "^17.0.1",
        "react-dom": "^17.0.1",
        "idom-client-react": "^0.8.5",
        ...
      },
      ...
    }

Getting a bit more in the weeds now, your ``rollup.config.js`` file should be designed
such that it drops an ES Module at ``your-project/your_python_package/bundle.js`` since
we'll be writing ``widget.py`` under that assumption.

.. note::

    Don't forget to ignore this ``bundle.js`` file when committing code (with a
    ``.gitignore`` if you're using Git) since it can always rebuild from the raw
    Javascript source in ``your-project/js``.

.. code-block:: javascript

    import resolve from "rollup-plugin-node-resolve";
    import commonjs from "rollup-plugin-commonjs";
    import replace from "rollup-plugin-replace";

    export default {
      input: "src/index.js",
      output: {
        file: "../your_python_package/bundle.js",
        format: "esm",
      },
      plugins: [
        resolve(),
        commonjs(),
        replace({
          "process.env.NODE_ENV": JSON.stringify("production"),
        }),
      ]
    };

Your ``widget.py`` file should then load the neighboring bundle file using
:func:`~idom.web.module.module_from_file`. Then components from that bundle can be
loaded with :func:`~idom.web.module.export`.

.. code-block::

    from pathlib import Path

    import idom

    _BUNDLE_PATH = Path(__file__).parent / "bundle.js"
    _WEB_MODULE = idom.web.module_from_file(
        # Note that this is the same name from package.json - this must be globally
        # unique since it must share a namespace with all other javascript packages.
        name="YOUR-PACKAGE-NAME",
        file=_BUNDLE_PATH,
        # What to temporarilly display while the module is being loaded
        fallback="Loading...",
    )

    # Your module must provide a named export for YourFirstComponent
    YourFirstComponent = idom.web.export(_WEB_MODULE, "YourFirstComponent")

    # It's possible to export multiple components at once
    YourSecondComponent, YourThirdComponent = idom.web.export(
        _WEB_MODULE, ["YourSecondComponent", "YourThirdComponent"]
    )

.. note::

    When :data:`idom.config.IDOM_DEBUG_MODE` is active, named exports will be validated.

The remaining files that we need to create are concerned with creating a Python package.
We won't cover all the details here, so refer to the Setuptools_ documentation for
more information. With that said, the first file to fill out is `pyproject.toml` since
we need to declare what our build tool is (in this case Setuptools):

.. code-block:: toml

    [build-system]
    requires = ["setuptools>=40.8.0", "wheel"]
    build-backend = "setuptools.build_meta"

Then, we can creat the ``setup.py`` file which uses Setuptools. This will differ
substantially from a normal ``setup.py`` file since, as part of the build process we'll
need to use NPM to bundle our Javascript. This requires customizing some of the build
commands in Setuptools like ``build``, ``sdist``, and ``develop``:

.. code-block:: python

    import subprocess
    from pathlib import Path

    from setuptools import setup, find_packages
    from distutils.command.build import build
    from distutils.command.sdist import sdist
    from setuptools.command.develop import develop

    PACKAGE_SPEC = {}  # gets passed to setup() at the end


    # -----------------------------------------------------------------------------
    # General Package Info
    # -----------------------------------------------------------------------------


    PACKAGE_NAME = "your_python_package"

    PACKAGE_SPEC.update(
        name=PACKAGE_NAME,
        version="0.0.1",
        packages=find_packages(exclude=["tests*"]),
        classifiers=["Framework :: IDOM", ...],
        keywords=["IDOM", "components", ...],
        # install IDOM with this package
        install_requires=["idom"],
        # required in order to include static files like bundle.js using MANIFEST.in
        include_package_data=True,
        # we need access to the file system, so cannot be run from a zip file
        zip_safe=False,
    )


    # ----------------------------------------------------------------------------
    # Build Javascript
    # ----------------------------------------------------------------------------


    # basic paths used to gather files
    PROJECT_ROOT = Path(__file__).parent
    PACKAGE_DIR = PROJECT_ROOT / PACKAGE_NAME
    JS_DIR = PROJECT_ROOT / "js"


    def build_javascript_first(cls):
        class Command(cls):
            def run(self):
                for cmd_str in ["npm install", "npm run build"]:
                    subprocess.run(cmd_str.split(), cwd=str(JS_DIR), check=True)
                super().run()

        return Command


    package["cmdclass"] = {
        "sdist": build_javascript_first(sdist),
        "build": build_javascript_first(build),
        "develop": build_javascript_first(develop),
    }


    # -----------------------------------------------------------------------------
    # Run It
    # -----------------------------------------------------------------------------


    if __name__ == "__main__":
        setup(**package)


Finally, since we're using ``include_package_data`` you'll need a MANIFEST.in_ file that
includes ``bundle.js``:

.. code-block:: text

    include your_python_package/bundle.js

And that's it! While this might seem like a lot of work, you're always free to start
creating your custom components using the provided `template repository`_ so you can get
up and running as quickly as possible.


.. Links
.. =====

.. _NPM: https://www.npmjs.com
.. _install NPM: https://www.npmjs.com/get-npm
.. _CDN: https://en.wikipedia.org/wiki/Content_delivery_network
.. _PyPI: https://pypi.org/
.. _template repository: https://github.com/idom-team/idom-react-component-cookiecutter
.. _web module: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules
.. _Rollup: https://rollupjs.org/guide/en/
.. _Webpack: https://webpack.js.org/
.. _Setuptools: https://setuptools.readthedocs.io/en/latest/userguide/index.html
.. _ECMAScript Module: https://tc39.es/ecma262/#sec-modules
.. _React: https://reactjs.org
.. _MANIFEST.in: https://packaging.python.org/guides/using-manifest-in/
