class Utilities {

	handleProxyUnauthorized() {
		alert('Your session has expired, please log in again.');
		window.location = '/auth/logout';
	}

	changeFavicon(iconSrc) {
		let ico = document.createElement('link');
		let old = document.getElementById('dynamic-favicon');
		ico.id = 'dynamic-favicon';
		ico.rel = 'shortcut icon';
		ico.href = iconSrc;
		if (old) old.remove();
		document.head.appendChild(ico);
	}

}

let utilities = new Utilities();