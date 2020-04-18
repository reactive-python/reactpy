import React from '../web_modules/react.js';
import { VictoryBar, VictoryChart, VictoryAxis } from '../web_modules/victory.js';
import htm from "../web_modules/htm.js";

const html = htm.bind(React.createElement);

const data = [
  { quarter: 1, earnings: 13000 },
  { quarter: 2, earnings: 16500 },
  { quarter: 3, earnings: 14250 },
  { quarter: 4, earnings: 19000 }
];

function Chart() {
  return html`
      <${VictoryChart} domainPadding=20>
        <${VictoryAxis}
          tickValues=${[1, 2, 3, 4]}
          tickFormat=${["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]}
        />
        <${VictoryAxis}
          dependentAxis
          tickFormat=${(x) => (`$${x / 1000}k`)}
        />
        <${VictoryBar}
          data=${data}
          x="quarter"
          y="earnings"
        />
      </${VictoryChart}>
    `
}

export default { Chart: Chart }