import React from "react";
import { transform as babelTransform } from "@babel/standalone";

function lazyComponent(model) {
    return React.lazy(() => {
        try {
            const result = evalInContext(model.importSource.source);
            // Allows the code to make components with dynamic imports that to return a
            // promise. Non-dynamic code, is just wrapped in a promise so it works with
            // React.lazy without any user code.
            return Promise.resolve(result).then(pkg => {
                return resolvePackage(pkg, model.tagName);
            });
        } catch (error) {
            function Error() {
                return (
                    <pre>
                        <code>{error.message}</code>
                    </pre>
                );
            }
            return Promise.resolve({ default: Error });
        }
    });
}

function resolvePackage(pkg, path) {
    let Resolution;
    try {
        const Component = getPathProperty(pkg, path);

        switch (typeof Component) {
            case "string":
            case "function":
                Resolution = props => {
                    return (
                        <ErrorBoundary>
                            <Component {...props} />
                        </ErrorBoundary>
                    );
                };
                break;
            default:
                Resolution = props => {
                    const msg =
                        "Element type is invalid: expected a string (for " +
                        "built-in components) or a class/function (for " +
                        "composite components) but got: undefined.";
                    return (
                        <pre>
                            <code>{msg}</code>
                        </pre>
                    );
                };
        }
    } catch (error) {
        Resolution = props => {
            return (
                <pre>
                    <code>{error.message}</code>
                </pre>
            );
        };
    }
    return { default: Resolution };
}

function getPathProperty(obj, prop) {
    // properties may be dot seperated strings
    const path = prop.split(".");
    const firstProp = path.shift();
    let value = obj[firstProp];
    for (let i = 0; i < path.length; i++) {
        value = value[path[i]];
    }
    return value;
}

function evalInContext(jsx) {
    const transform = babelTransform(
        "() => {let React = this.React;" + jsx + "}",
        {
            presets: ["react"],
            plugins: [require("@babel/plugin-syntax-dynamic-import")]
        }
    );
    return function() {
        return eval(transform.code)();
    }.call({
        React: React
    });
}

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null
        };
    }
    componentDidCatch(error, info) {
        this.setState({
            error: error.message
        });
        console.log("error: ", error);
        console.log("info: ", info);
    }
    render() {
        if (this.state.error) {
            return (
                <pre>
                    <code>{this.state.error}</code>
                </pre>
            );
        }
        return this.props.children;
    }
}

export default lazyComponent;
