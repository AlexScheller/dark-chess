class Utilities {

	handleProxyUnauthorized() {
		alert('Your session has expired, please log in again.');
		window.location = '/auth/logout';
	}

}

let utilities = new Utilities();