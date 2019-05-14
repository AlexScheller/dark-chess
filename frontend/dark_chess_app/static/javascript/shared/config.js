class Config {

	constructor(options) {
		if ('debug' in options) {
			this.debug = options.debug;
		} else {
			this.debug = false;
		}
		// temporary while in development
		this.apiRoot = 'http://localhost:5000';
	}

	static optionsFromHTML() {
		const configParams = document.getElementById('config-params');
		let options = {
			debug: configParams.dataset.debug === 'True' ? true : false
		};
		return options;
	}

}

let config = new Config(Config.optionsFromHTML());