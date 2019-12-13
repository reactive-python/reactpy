import React from "react";

function lazyComponent(model) {
    return React.lazy(() => {
        try {
            return eval(`import('${model.importSource.source}')`).then(
                pkg => {
                    pkg = pkg.default ? pkg.default : pkg;
                    return resolvePackage(pkg, model.tagName);
                },
                error => {
                    function Catch() {
                        return (
                            <pre>
                                <code>{error.stack}</code>
                            </pre>
                        );
                    }
                    return { default: Catch };
                }
            );
        } catch (error) {
            function Error() {
                return (
                    <pre>
                        <code>{error.stack}</code>
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
        const Component = path ? getPathProperty(pkg, path) : pkg;

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
                    <code>{this.state.error.stack}</code>
                </pre>
            );
        }
        return this.props.children;
    }
}

export default lazyComponent;
