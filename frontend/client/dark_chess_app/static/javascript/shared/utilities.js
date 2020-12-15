class Utilities {

	handleProxyUnauthorized() {
		alert('Your session has expired, please log in again.');
		window.location = '/auth/logout';
	}

	changeFavicon(iconFile) {
		let old = document.getElementById('dynamic-favicon');
		if (old) {
			// No reason to change the favicon if the same one is being
			// requested.
			let currentIcon = old.href.split("/").pop();
			if (currentIcon !== iconFile) {
				console.log('changing icon');
				let ico = document.createElement('link');
				ico.id = 'dynamic-favicon';
				ico.rel = 'shortcut icon';
				ico.href = `${config.clientRoot}/static/images/${iconFile}`;
				if (old) old.remove();
				document.head.appendChild(ico);
			}
		} else {
			let ico = document.createElement('link');
			ico.id = 'dynamic-favicon';
			ico.rel = 'shortcut icon';
			ico.href = `${config.clientRoot}/static/images/${iconFile}`;
			document.head.appendChild(ico);
		}
	}

}

let utilities = new Utilities();