let toggles = document.querySelectorAll('input[type=checkbox]');
for (const toggle of toggles) {
	toggle.addEventListener('change', event => {
		toggle.parentElement.parentElement.classList.toggle('checked');
	});
}