class Config {

	constructor(options) {
		if ('token' in options) {
			this.token = options.token;
		} else {
			this.token = null;
		}
		// temporary while in development
		this.apiRoot = 'http://localhost:5000'
	}

}