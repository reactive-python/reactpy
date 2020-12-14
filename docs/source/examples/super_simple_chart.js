import React from "./react.js";
import htm from "./htm.js";

const html = htm.bind(React.createElement);

export function SuperSimpleChart(props) {
  const data = props.data;
  const lastDataIndex = data.length - 1;

  const options = {
    height: props.height || 100,
    width: props.width || 100,
    color: props.color || "blue",
    lineWidth: props.lineWidth || 2,
    axisColor: props.axisColor || "black",
  };

  const xData = data.map((point) => point.x);
  const yData = data.map((point) => point.y);

  const domain = {
    xMin: Math.min(...xData),
    xMax: Math.max(...xData),
    yMin: Math.min(...yData),
    yMax: Math.max(...yData),
  };

  return html`<svg
    width="${options.width}px"
    height="${options.height}px"
    viewBox="0 0 ${options.width} ${options.height}"
  >
    ${makePath(props, domain, data, options)} ${makeAxis(props, options)}
  </svg>`;
}

function makePath(props, domain, data, options) {
  const { xMin, xMax, yMin, yMax } = domain;
  const { width, height } = options;
  const getSvgX = (x) => ((x - xMin) / (xMax - xMin)) * width;
  const getSvgY = (y) => height - ((y - yMin) / (yMax - yMin)) * height;

  let pathD = "M " + getSvgX(data[0].x) + " " + getSvgY(data[0].y) + " ";
  pathD += data.map((point, i) => {
    return "L " + getSvgX(point.x) + " " + getSvgY(point.y) + " ";
  });

  return html`<path
    d="${pathD}"
    style=${{
      stroke: options.color,
      strokeWidth: options.lineWidth,
      fill: "none",
    }}
  />`;
}

function makeAxis(props, options) {
  return html`<g>
    <line
      x1="0"
      y1=${options.height}
      x2=${options.width}
      y2=${options.height}
      style=${{ stroke: options.axisColor, strokeWidth: options.lineWidth * 2 }}
    />
    <line
      x1="0"
      y1="0"
      x2="0"
      y2=${options.height}
      style=${{ stroke: options.axisColor, strokeWidth: options.lineWidth * 2 }}
    />
  </g>`;
}
