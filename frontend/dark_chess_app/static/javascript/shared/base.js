let toggles = document.querySelectorAll('input[type=checkbox]');
for (const toggle of toggles) {
	toggle.addEventListener('change', event => {
		toggle.parentElement.parentElement.classList.toggle('checked');
	});
}

let deleteFlashes = document.getElementsByClassName('delete-flash-message-button');
for (const deleteFlash of deleteFlashes) {
	deleteFlash.addEventListener('click', event => {
		let id = event.currentTarget.dataset.flashMessageId;
		document.getElementById(id).remove();
	});
}