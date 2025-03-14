// Sync scrolling between the code node and the line number node
// Event needs to be a separate function, otherwise the event will be triggered multiple times
let code_with_lineno_scroll_event = function () {
	let tr = this.parentNode.parentNode.parentNode.parentNode;
	let lineno = tr.querySelector(".linenos");
	lineno.scrollTop = this.scrollTop;
};

const observer = new MutationObserver((mutations) => {
	let lineno = document.querySelectorAll(".linenos~.code");
	lineno.forEach(function (element) {
		let code = element.parentNode.querySelector("code");
		code.addEventListener("scroll", code_with_lineno_scroll_event);
	});
});

observer.observe(document.body, {
	childList: true,
});
