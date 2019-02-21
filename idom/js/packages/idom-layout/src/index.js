import React, { useReducer, useEffect, useState, useMemo } from 'react';
import produce from 'immer';


function Layout({ socket }) {
    const [root, setRoot] = useState(null);
    const [models, setModels] = useState({});

    socket.onmessage = event => {
      const msg = JSON.parse(event.data);
      setRoot(msg.header.root);
      const newModels = { ...models, ...msg.body.models };
      setModels(newModels);
    }

    const sendMsg = msg => { socket.send(JSON.stringify(msg)) }

    if (root == null || !models.hasOwnProperty(root) ) {
        return <div />;
    } else {
        return Element(models, root, event => {
            sendMsg({
                header: {},
                body: { event: event }
            });
        });
    }
}


function Element(models, id, sendEvent) {
    const model = models[id];

    const children = model.children.map(child => {
        switch (child.type) {
            case 'ref':
                return Element(models[child.data]);
            case 'obj':
                return Element(child.data);
            case 'str':
                return child.data;
        }
    });

    const attributes = Object.assign({}, model.attributes);

    Object.keys(model.eventHandlers).forEach(target => {
        const [handler, eventName] = model.eventHandlers[target].split('_');
        attributes[eventName] = event => {
          console.log(event);
          sendEvent({
              target: target,
              handler: handler,
              data: null
          });
        };
    });

    let Tag = model.tagName;
    if (children.length) {
        return <Tag {...attributes}>{children}</Tag>;
    } else {
        return <Tag {...attributes} />;
    }
}


export default Layout;
