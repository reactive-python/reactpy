import React, { useReducer, useEffect, useState, useMemo } from 'react';
import produce from 'immer';


function Layout({ socket }) {
    const [root, setRoot] = useState(null);
    const [allModels, setAllModels] = useState({});

    socket.onmessage = event => {
      const msg = JSON.parse(event.data);
      setRoot(msg.header.root);
      const newModels = { ...allModels, ...msg.body.models };
      setAllModels(newModels);
    }

    const sendMsg = msg => { socket.send(JSON.stringify(msg)) }
    const sendEvent = event => {
        sendMsg({
            header: {},
            body: { event: event }
        });
    };

    if (root == null || !allModels.hasOwnProperty(root) ) {
        return <div />;
    } else {
        return Element(allModels, allModels[root], sendEvent);
    }
}


function Element(allModels, model, sendEvent) {

    const children = model.children.map(child => {
        switch (child.type) {
            case 'ref':
                return Element(allModels, allModels[child.data], sendEvent);
            case 'obj':
                return Element(allModels, child.data, sendEvent);
            case 'str':
                return child.data;
        }
    });

    const attributes = Object.assign({}, model.attributes);

    Object.keys(model.eventHandlers).forEach(target => {
        const [handler, eventDef] = model.eventHandlers[target].split('_');
        const eventParts = eventDef.split("-");
        const eventName = eventParts.shift();
        attributes[eventName] = event => {
          const data = {};
          eventParts.forEach(n => {
            data[n] = event[n];
          })
          sendEvent({
              target: target,
              handler: handler,
              data: data
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
