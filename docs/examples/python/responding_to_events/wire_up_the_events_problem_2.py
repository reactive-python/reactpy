from reactpy import component, html
from reactpy import use_state
from "./ColorSwitch" import color_switch

def app():
	const (clicks, set_clicks) = use_state(0)

	def handle_click_outside():
		set_clicks(lambda )

export default function App() {
	const [clicks, setClicks] = useState(0);

	function handleClickOutside() {
		setClicks((c) => c + 1);
	}

	function getRandomLightColor() {
		let r = 150 + Math.round(100 * Math.random());
		let g = 150 + Math.round(100 * Math.random());
		let b = 150 + Math.round(100 * Math.random());
		return `rgb(${r}, ${g}, ${b})`;
	}

	function handleChangeColor() {
		let bodyStyle = document.body.style;
		bodyStyle.backgroundColor = getRandomLightColor();
	}

	return (
		<div
			style={{ width: "100%", height: "100%" }}
			on_click={handleClickOutside}
		>
			<ColorSwitch onChangeColor={handleChangeColor} />
			<br />
			<br />
			<h2>Clicks on the page: {clicks}</h2>
		</div>
	);
}