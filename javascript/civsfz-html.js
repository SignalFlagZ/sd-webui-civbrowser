"use strict";

onUiLoaded(civbrowser_start_it_up);
function civbrowser_start_it_up() {
	//make tab sticky
	let elem = gradioApp().querySelector('#civsfz_tab-element').firstChild;
	elem.classList.add("civsfz-sticky-element");
	elem.classList.add("civsfz-tabbar");

	// Observe scroll positions
	const tabs = gradioApp().querySelectorAll('.civsfz-tab-item');
	tabs.forEach((tab) => {
		const id = tab.getAttribute("id");
		sessionStorage.setItem(id, 0); // init
		// Observe whether the tab is displayed.

		const observer_tab = new MutationObserver((mutationsList) => {
			for (const mutation of mutationsList) {
				if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
					// style changed
					if (window.getComputedStyle(tab).display === 'none') {
						// Hidden
					} else {
						// Visible  display: block
						// restore scroll position
						const lastScrollTop = sessionStorage.getItem(id);
						if (lastScrollTop != null) {
							window.scrollTo({ top: parseInt(lastScrollTop), behavior: 'smooth' });
						}
					}
				}
			}
		});
		// Start of observation
		observer_tab.observe(tab, { attributes: true }); 
	});

	// Observe civbrowser tab
	const civtab = gradioApp().querySelector('#tab_civsfz_interface');
	const observer_civtab = new MutationObserver((mutationsList) => {

		for (const mutation of mutationsList) {
			if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
				// style changed
				if (window.getComputedStyle(civtab).display === 'none') {
					// Hidden
				} else {
					tabs.forEach((tab) => {
						if (window.getComputedStyle(tab).display === 'block') {
							const id = tab.getAttribute("id");
							const lastScrollTop = sessionStorage.getItem(id);
							if (lastScrollTop != null) {
								window.scrollTo({ top: parseInt(lastScrollTop), behavior: 'smooth' });
							}
						}
					})
				}
			}
		}
	});
	// Start of observation
	observer_civtab.observe(civtab, { attributes: true }); 

	// Add scrollend event 
	// save scroll position
	const handle_scroll = (evt) => {
		const tabs = evt.srcElement.querySelectorAll('.civsfz-tab-item');
		tabs.forEach((tab) => {
			const id = tab.getAttribute("id");
			if (tab.checkVisibility()) {
				// Visible
				// console.log(id + ":" + window.scrollY);
				sessionStorage.setItem(id, window.scrollY);
			}
		})
	};
	window.addEventListener("scrollend", handle_scroll);
}

// click & scroll
function civsfz_click_and_scroll(selector, scrollSelector = "#tabs") {
	const elem = gradioApp().querySelector(selector);
	if (elem) {
		elem.click();
	}
	setTimeout(() => {
		civsfz_scroll_to(scrollSelector);
	}, 200);
}

function civsfz_select_model(model_name) {
	console.log(model_name);
	// model_name-> selector:tab_id:
	const regex1 = /(^.+?)(\d):/;
	let match = regex1.exec(model_name);
	//console.log(match);
	if (match[1] == 'Index') {
		civsfz_scroll_to('#civsfz_model-data' + match[2]);
		let selector = '#civsfz_eventtext' + match[2] + ' textarea';
		let model_dropdown = gradioApp().querySelector(selector);
		if (model_dropdown && model_name) {
			/*Force card click event*/
			model_dropdown.value = model_name + ':' + civsfz_getRandomIntInclusive(0, 9999);
			updateInput(model_dropdown);
		}
	}
}

function civsfz_update_textbox(ID, text) {
	//console.log(text)
	let selector = ID + ' textarea';
	let textbox = gradioApp().querySelector(selector);
	if (textbox) {
		/*Force event*/
		textbox.value = text;
		updateInput(textbox);
	}
}

function civsfz_cancel_download(path) {
	// Cancel download
	//console.log(text)
	path = decodeURI(path);
	let id = '#civsfz_eventtext_dl';
	if (path) {
		let text = 'CancelDl??' + path + '??' + civsfz_getRandomIntInclusive(0, 9999);
		civsfz_update_textbox(id, text);
	}
}

function civsfz_open_folder(path) {
	// Cancel download
	//console.log(text)
	path = decodeURI(path);
	let id = '#civsfz_eventtext_dl';
	if (path) {
		let text = 'OpenFolder??' + path + '??' + civsfz_getRandomIntInclusive(0, 9999);
		civsfz_update_textbox(id, text);
	}
}

/*https://developer.mozilla.org/ja/docs/Web/JavaScript/Reference/Global_Objects/Math/random#%E5%8C%85%E6%8B%AC%E7%9A%84%E3%81%AB_2_%E3%81%A4%E3%81%AE%E5%80%A4%E3%81%AE%E9%96%93%E3%81%AE%E3%83%A9%E3%83%B3%E3%83%80%E3%83%A0%E3%81%AA%E6%95%B4%E6%95%B0%E3%82%92%E5%BE%97%E3%82%8B*/
function civsfz_getRandomIntInclusive(min, max) {
	min = Math.ceil(min);
	max = Math.floor(max);
	return Math.floor(Math.random() * (max - min + 1) + min); //The maximum is inclusive and the minimum is inclusive
}

function civsfz_trigger_event(element, event) {
	let e = new Event(event);
	Object.defineProperty(e, "target", { value: element });
	//element.focus();
	element.dispatchEvent(e);
}
function civsfz_trigger_key_down(element, key) {
	let e = new KeyboardEvent("keydown", { key: key });
	//element.focus();
	element.dispatchEvent(e);
}

function civsfz_send2txt2img(text, send = true) {
	//console.log(text)
	try {
		text = decodeURI(text);
	} catch (e) {
		//
	}
	if (send) {
		let response = confirm("Send to txt2img?");
		if (response) {
			let prompt = gradioApp().querySelector('#txt2img_prompt textarea');
			let paste = '#paste';
			if (gradioApp().querySelector(paste) == null) {
				//SD.Next
				paste = '#txt2img_paste';
			}
			prompt.value = text;
			civsfz_trigger_event(prompt, 'input');
			civsfz_click_and_scroll(paste);
			//trigger_key_down(prompt, 'Escape');
		}
	} else {
		return navigator.clipboard.writeText(text)
			.then(
				function () {
					alert("Copied " + text);
				}
			).catch(
				function (error) {
					alert((error && error.message) || "Failed to copy infotext");
				}
			)
	}
}

function civsfz_copyInnerText(node, send = true) {
	if (node.nextSibling != null) {
		//let ret = navigator.clipboard.writeText(node.nextSibling.innerText;
		//alert("Copied infotext");
		if (send) {
			let response = confirm("Send to txt2img?");
			if (response) {
				let prompt = gradioApp().querySelector('#txt2img_prompt textarea');
				let paste = gradioApp().querySelector('#paste');
				if (paste == null) {
					//SD.Next
					paste = gradioApp().querySelector('#txt2img_paste');
				}
				prompt.value = node.nextElementSibling.innerText;
				civsfz_trigger_event(prompt, 'input');
				civsfz_trigger_event(paste, 'click');
				//trigger_key_down(prompt, 'Escape');
			}
		} else {
			return navigator.clipboard.writeText(node.nextElementSibling.innerText.trim())
				.then(
					function () {
						alert("Copied " + node.nextElementSibling.innerText.trim());
					}
				).catch(
					function (error) {
						alert((error && error.message) || "Failed to copy infotext");
					}
				)
		}
	}
}

function civsfz_overwriteProperties(propertiesText) {
	//let propertiesText = gradioApp().querySelector('#' + elem_id + ' textarea').value;
	//console.log(elem_id, propertiesText)
	let p = propertiesText.split(';');
	let elem = gradioApp().querySelector('.civsfz-custom-property');
	let i = 0
	//elements.forEach((elem) => {
	elem.style.setProperty('--civsfz-background-color-figcaption', p[i++]);
	elem.style.setProperty('--civsfz-shadow-color-default', p[i++] + 'f0');
	elem.style.setProperty('--civsfz-shadow-color-alreadyhave', p[i++] + 'f0');
	elem.style.setProperty('--civsfz-shadow-color-alreadyhad', p[i++] + 'f0');
	elem.style.setProperty('--civsfz-hover-scale', p[i++]);
	elem.style.setProperty('--civsfz-card-width', p[i++]);
	elem.style.setProperty('--civsfz-card-height', p[i++]);
	//Color Family
	const fColors = JSON.parse(p[i]);
	Object.keys(fColors).forEach(function (key) {
		let color = fColors[key]
		let prop = '--civsfz-color-for-' + key.replace(/[\ \.]/g, '_')
		elem.style.setProperty(prop, color);
	})
	//});
}

function civsfz_querySelectSetProperty(q, p, c) {
	let elements = gradioApp().querySelectorAll(q);
	elements.forEach((elem) => {
		elem.style.setProperty(p, c);
	});
}

function civsfz_scroll_to(q, offset = -50) {
	const elem = gradioApp().querySelector(q);
	if (elem) {
		const y = elem.getBoundingClientRect().top + window.scrollY + offset;
		window.scrollTo({ top: y, behavior: 'smooth' });
	}
}

function civsfz_preview_colors() {
	for (var i = 1; i <= 10; i++) {
		let elmDropdwn = gradioApp().querySelector('#setting_civsfz_family' + i.toString(10));
		if (elmDropdwn == null) { break; }
		let elmColor = gradioApp().querySelector('#setting_civsfz_color_family' + i.toString(10));
		let color = elmColor.querySelector("input").value;
		//console.log(color);
		let tokens = elmDropdwn.getElementsByClassName("token");
		let len = tokens.length;
		let hasBg = len > 0 ? tokens[0].style.getPropertyValue("background") : false;
		for (let j=0; j < tokens.length; j++) {
			let token = tokens[j];
			if (!hasBg) {
				let h_param = 30 / (len / 3) * Math.floor(j/4);
				let l_param = (1 - j % 4 / 5)* 0.6 + 0.4;
				let s_param = 0.5/len*(len-j) + 0.5;
				token.style.setProperty("background",`hsl(from ${color} calc(h + ${h_param}) calc(s*${s_param}) calc(l*${l_param})`);
			} else {
				token.style.removeProperty("background");
			}
		}
	}
}

function civsfz_scroll_and_color(q, id, l ){
	civsfz_scroll_to(q);
	civsfz_version_color(id, l);
}

function civsfz_version_color(id, l) {
	//console.log(l);
	let versions = JSON.parse(l);
	let elmVersionRadio = gradioApp().querySelector(id);
	if (elmVersionRadio == null) { return; }
	let labels = elmVersionRadio.getElementsByTagName("label");
	for (let j = 0; j < labels.length; j++) {
		let label = labels[j];
		// let span = label.getElementsByTagName("span")[0];
		// console.log(label);
		let color = "var(--civsfz-color-for-" + versions[j]["base_model"].replace(/[\ \.]/g, '_');
		label.style.setProperty("border-bottom", "solid 4px " + color);
		if (versions[j]["have"]) {
			label.style.setProperty("border-top", "solid 2px var(--civsfz-shadow-color-alreadyhave)");
		} else {
			label.style.removeProperty("border-top");
		}
	}
}

function civsfz_throttle(func, delay) {
	let lastRan = 0;
	return function (...args) {
		const now = new Date().getTime();
		if (now - lastRan >= delay) {
			lastRan = now;
			func.apply(this, args);
		}
	};
}
