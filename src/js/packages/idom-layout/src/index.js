import React, {
    useReducer,
    useEffect,
    useState,
    useMemo,
    lazy,
    Suspense
} from "react";
import { transform as babelTransform } from "@babel/standalone";

import serializeEvent from "./event-to-object";

const allUpdateTriggers = {};
const allModels = {};

function updateDynamicElement(elementId) {
    if (allUpdateTriggers.hasOwnProperty(elementId)) {
        allUpdateTriggers[elementId]();
    }
}

function Layout({ endpoint }) {
    // handle relative endpoint URI
    if (endpoint.startsWith(".") || endpoint.startsWith("/")) {
        let loc = window.location;
        let protocol;
        if (loc.protocol === "https:") {
            protocol = "wss:";
        } else {
            protocol = "ws:";
        }
        let new_uri = protocol + "//" + loc.host;
        if (endpoint.startsWith(".")) {
            new_url += loc.pathname + "/";
        }
        endpoint = new_uri + endpoint;
    }

    const socket = useMemo(() => {
        return new WebSocket(endpoint);
    }, [endpoint]);

    const [root, setRoot] = useState(null);

    socket.onmessage = event => {
        const msg = JSON.parse(event.data);
        Object.assign(allModels, msg.body.render.new);
        msg.body.render.old.forEach(elementId => {
            delete allModels[elementId];
        });
        updateDynamicElement(msg.body.render.src);
        if (!root) {
            setRoot(msg.body.render.root);
        }
    };

    const sendMsg = msg => {
        socket.send(JSON.stringify(msg));
    };
    const sendEvent = event => {
        sendMsg({
            header: {},
            body: { event: event }
        });
    };

    if (root) {
        return <DynamicElement elementId={root} sendEvent={sendEvent} />;
    } else {
        return <div />;
    }
}

function DynamicElement({ elementId, sendEvent }) {
    allUpdateTriggers[elementId] = useForceUpdate();
    const model = allModels[elementId];
    if (model) {
        return <Element model={model} sendEvent={sendEvent} />;
    } else {
        return <div />;
    }
}

function Element({ model, sendEvent }) {
    const children = elementChildren(model, sendEvent);
    const attributes = elementAttributes(model, sendEvent);
    if (model.importSource) {
        const lazy = lazyComponent(model);
        return (
            <Suspense fallback={model.importSource.fallback}>
                {React.createElement(lazy, attributes, children)}
            </Suspense>
        );
    } else if (model.children && model.children.length) {
        return React.createElement(model.tagName, attributes, children);
    } else {
        return React.createElement(model.tagName, attributes);
    }
}

function elementChildren(model, sendEvent) {
    if (!model.children) {
        return [];
    } else {
        return model.children.map(child => {
            switch (child.type) {
                case "ref":
                    return (
                        <DynamicElement
                            elementId={child.data}
                            sendEvent={sendEvent}
                        />
                    );
                case "obj":
                    return <Element model={child.data} sendEvent={sendEvent} />;
                case "str":
                    return child.data;
            }
        });
    }
}

function elementAttributes(model, sendEvent) {
    const attributes = Object.assign({}, model.attributes);

    if (model.eventHandlers) {
        Object.keys(model.eventHandlers).forEach(eventName => {
            const eventSpec = model.eventHandlers[eventName];
            attributes[eventName] = function(event) {
                const data = Array.from(arguments).map(value => {
                    if (typeof value === "object" && value.nativeEvent) {
                        if (eventSpec["preventDefault"]) {
                            value.preventDefault();
                        }
                        if (eventSpec["stopPropagation"]) {
                            value.stopPropagation();
                        }
                        return serializeEvent(value);
                    } else {
                        return value;
                    }
                });
                const sentEvent = new Promise((resolve, reject) => {
                    const msg = {
                        data: data,
                        target: eventSpec["target"]
                    };
                    sendEvent(msg);
                    resolve(msg);
                });
            };
        });
    }

    return attributes;
}

function lazyComponent(model) {
    return React.lazy(() => {
        try {
            const result = evalInContext(model.importSource.source);
            // Allows the code to make components with dynamic imports that to return a
            // promise. Non-dynamic code, is just wrapped in a promise so it works with
            // React.lazy without any user code.
            return Promise.resolve(result).then(pkg => {
                const toExport = { default: pkg };
                model.tagName.split(".").forEach(part => {
                    toExport.default = toExport.default[part];
                });
                const Component = toExport.default;
                function Catch(props) {
                    return (
                        <ErrorBoundary>
                            <Component {...props} />
                        </ErrorBoundary>
                    );
                }
                return { default: Catch };
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

function useForceUpdate() {
    const [, setState] = useState(true);
    const forceUpdate = () => {
        setState(state => !state);
    };
    return forceUpdate;
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

export default Layout;
