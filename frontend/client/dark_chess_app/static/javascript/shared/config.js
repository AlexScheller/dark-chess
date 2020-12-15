class Config {

	constructor(options) {
		if ('debug' in options) {
			this.debug = options.debug;
		} else {
			this.debug = false;
		}
		if ('apiRoot' in options) {
			this.apiRoot = options.apiRoot;
		} else {
			this.apiRoot = 'http://localhost:5000';			
		}
	}

	get clientRoot() {
		return `${window.location.protocol}//${window.location.host}`;
	}

	static optionsFromHTML() {
		const configParams = document.getElementById('config-params');
		let options = {
			debug: configParams.dataset.debug === 'True' ? true : false
		};
		if ('apiRoot' in configParams.dataset) {
			options['apiRoot'] = configParams.dataset.apiRoot
		}
		return options;
	}

}

let config = new Config(Config.optionsFromHTML());