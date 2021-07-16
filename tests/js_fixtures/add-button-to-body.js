const button = document.createElement("button");
button.setAttribute("id", "the-button");
button.appendChild(document.createTextNode("click me!"));
button.onclick = () => {document.body.removeChild(button)};

document.body.appendChild(button);
