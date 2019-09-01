let schemaHeaders = document.getElementsByClassName('schema-header');
for (const header of schemaHeaders) {
	header.addEventListener('click', event => {
		header.nextElementSibling.classList.toggle('hidden');
	});
}

let navLinks = document.querySelectorAll('.nav-link a');
for (const navLink of navLinks) {
	navLink.addEventListener('click', event => {
		let schema = document.getElementById(navLink.dataset.navTarget);
		schema.childNodes[3].classList.toggle('hidden');
	});
}

// function switchTab(tabHeader, schemaId, code) {
// 	let selected = document.querySelector(
// 		'#' + schemaId + ' .tab-headers .tab-header.selected'
// 	);
// 	selected.classList.remove('selected');
// 	tabHeader.classList.add('selected')
// 	let oldShown = document.querySelector('#' + schemaId + ' .tab-content:not(.hidden)');
// 	oldShown.classList.add('hidden');
// 	let newShown = document.getElementById(schemaId + '-' + code + '-tab');
// 	newShown.classList.remove('hidden');
// }

let tabHeaders = document.getElementsByClassName('tab-header');
for (const tabHeader of tabHeaders) {
	tabHeader.addEventListener('click', event => {
		let schemaId = event.target.dataset.schemaId;
		let responseCode = event.target.dataset.responseCode;
		let selected = document.querySelector(
			'#' + schemaId + ' .tab-headers .tab-header.selected'
		);
		selected.classList.remove('selected');
		tabHeader.classList.add('selected')
		let oldShown = document.querySelector('#' + schemaId + ' .tab-content:not(.hidden)');
		oldShown.classList.add('hidden');
		let newShown = document.getElementById(schemaId + '-' + responseCode + '-tab');
		newShown.classList.remove('hidden');
	});
}