class Config {

	constructor(options) {
		if ('token' in options) {
			this.token = options.token;
		} else {
			this.token = null;
		}
		if ('debug' in options) {
			this.debug = options.debug;
		} else {
			this.debug = false;
		}
		// temporary while in development
		this.apiRoot = 'http://localhost:5000'
	}

}