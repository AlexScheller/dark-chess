// WebsocketHandler listens to events from the backend on behalf of the
// other classes.
class WebsocketHandler {

	constructor(config) {
		if (config.debug) {
			console.debug('Constructing WebsocketHandler.');
		}
		this._conn = this._setupServerConn(config.apiRoot);
		this._registerEventListeners();
	}

	setListener(listener) {
		this._listener = listener;
	}

	_setupServerConn(url) {
		if (config.debug) {
			console.debug('Setting up server connection.')
		}
		return io(url + '/match-moves');
	}

	_registerEventListeners() {
		if (config.debug) {
			console.debug('Registering ws event listeners.');
		}
		this._conn.on('connect', event => {
			if (config.debug) {
				console.debug('Connected to server.');
				console.debug('Authenticating...');
			}
			this._conn.emit('authenticate', {token: config.token});
		});
		this._conn.on('authenticated', event => {
			if (config.debug) {
				console.debug('Authenticated');
				console.debug(event);
			}
		});
		this._conn.on('move-made', event => {
			if (config.debug) {
				console.debug('Move made');
				console.debug(event);
			}
			this._listener.handleMoveEvent(event);
		});
	}

}


// APIHandler makes requests to the api on behalf of the other classes.
class APIHandler {

	constructor(config) {
		if (config.debug) {
			console.debug('Constructing APIHandler.');
		}
		this.apiUrl = config.apiRoot;
	}

	syncMatchState(model) {
		fetch(`${this.apiUrl}/match/${model.matchId}`, {
			method: 'GET',
			headers: {
				'Authorization': `Bearer ${config.token}`
			}
		}).then(response => {
			return response.json();
		}).then(json => {
			model.reload(json.current_fen);
		});
	}

	requestMove(model, move) {
		if (config.debug) {
			console.debug('(API Event) requesting move: ' + move);
		}
		fetch(`${this.apiUrl}/match/${model.matchId}/make-move`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${config.token}`
			},
			body: JSON.stringify({
				uci_string: move
			})
		}).then(response => {
			return response.json();
		}).then(json => {
			if (config.debug) {
				console.debug('(Server Response)');
				console.log(json);
			}
			// Do nothing with a successful request, as it will trigger
			// a websocket event from the server. That event is then handled
			// elsewhere.
		});
	}

}

// This is just a client cache for the backend's model. Its main
// intention is to allow client-side move verification.
class MatchModel {

	constructor(matchData, playerData) {
		if (config.debug) {
			console.debug('Constructing MatchModel.');
		}
		this._board = new Chess();
		// console.log(matchData.history[matchData.history.length - 1]);
		this._board.load(matchData.history[matchData.history.length - 1]);
		this.matchId = matchData.id;
		this._playerId = playerData.id;
		if (('player_black' in matchData) &&
			(matchData.player_black.id == this._playerId)) {
			this._playerSide = 'b';
		} else if (('player_white' in matchData) &&
			(matchData.player_white.id == this._playerId)) {
			this._playerSide = 'w';
		} else {
			this._playerSide = null;
		}
	}

	setListener(listener) {
		this._listener = listener;
	}

	reload(fen) {
		let successful = this._board.load(fen);
		if (successful) {
			this._listener.handleModelReload();
		} else {
			console.error(`Unable to load board from fen: ${fen}`)
		}
	}

	playersTurn() {
		if (this._playerSide == null) {
			return false;
		}
		return this._board.turn() == this._playerSide;
	}

	playersPiece(square) {
		let bSquare = this._board.get(square);
		if (bSquare == null || this._playerSide == null) {
			return null;
		}
		return this._playerSide == bSquare.color;
	}

	// expects same notation as used by backend, namely uci
	validMove(move) {
		return this._board.move(move, {sloppy: true}) != null;
	}

	pieceAt(square) {
		return this._board.get(square);
	}

	movesFrom(fromSquare) {
		return this._board.moves({
			verbose: true
		}).filter(move => move.from == fromSquare);
	}

}


// Like the class name implies, this controls the board view. It
// handles all player actions.
class BoardViewController {

	constructor(model) {
		if (config.debug) {
			console.debug('Constructing BoardViewController.')
		}
		this._pieceNames = {
			p: 'pawn', r: 'rook', n: 'knight',
			b: 'bishop', k: 'king', q: 'queen'
		}
		this._setupClickHandlers();
		this._model = model;
		this._model.setListener(this);
		this._selectedSquare = null;
		this._render();
	}

	setListener(listener) {
		this._listener = listener;
	}

	_setupClickHandlers() {
		let squares = document.getElementsByClassName('board-square');
		for (const square of squares) {
			square.addEventListener('click', event =>
				this._handleSquareClick(event)
			);
		}
	}

	_renderMoveOptions(fromSquare) {
		if (config.debug) {
			console.debug('(Render Event) rendering move options');
		}
		this._selectedSquare = fromSquare;
		document.getElementById(fromSquare).classList.add('selected-square');
		for (const move of this._model.movesFrom(fromSquare)) {
			if (config.debug) {
				console.debug('(Render Event) rendering move option: ' + fromSquare + move.to);
			}
			document.getElementById(move.to).classList.add('move-option');
		}
	}

	_clearRenderedMoveOptions() {
		if (config.debug) {
			console.debug('(Render Event) clearing rendered move options');
		}
		document.getElementById(this._selectedSquare).classList.remove('selected-square')
		this._selectedSquare = null;
		let options = document.querySelectorAll('.board-square.move-option');
		for (const option of options) {
			if (config.debug) {
				console.debug('(Render Event) clearing \'move-option\' from square: ' + option.id);
			}
			option.classList.remove('move-option');
		}
	}

	_handleSquareClick(event) {
		let square = event.currentTarget.id;
		if (config.debug) {
			let pieceJSON = JSON.stringify(this._model.pieceAt(square));
			console.debug('(Click Event) Piece at ' + square + ': ' + pieceJSON);
		}
		if (this._model.playersTurn()) {
			if (event.target.classList.contains('move-option')) {
				let move = this._selectedSquare + square;
				this._listener.moveRequest(move);
			} else if (this._model.playersPiece(square)) {
				this._renderMoveOptions(square);
			}
		}
	}

	// Probably faster to inline this up top but this is a lot cleaner.
	_renderPieceIconHTML(side, piece) {
		let weight = (side == 'b') ? 's' : 'l';
		return `
			<i class="fa${weight} fa-chess-${this._pieceNames[piece]} piece"></i>
		`
	}

	_render() {
		for (let row = 1; row <= 8; row++) {
			for (const col of 'abcdefgh') {
				let piece = this._model.pieceAt(col + row);
				let square = document.getElementById(col + row);
				if (piece != null) {
					let pieceHTML = this._renderPieceIconHTML(
						piece.color, piece.type
					);
					square.innerHTML = pieceHTML;
				} else {
					square.innerHTML = '';
				}
			}
		}
	}

	/* ModelListener methods */
	handleModelReload() {
		this._clearRenderedMoveOptions();
		this._render();
	}

}

// Main class
class Match {
	
	constructor(config, matchData, playerData) {
		this._mm = new MatchModel(matchData, playerData);
		this._bvc = new BoardViewController(this._mm);
		this._bvc.setListener(this);
		this._api = new APIHandler(config);
		this._wsh = new WebsocketHandler(config);
		this._wsh.setListener(this);
	}

	/* Board View Controller Listener methods */
	handleMoveRequest(move) {
		this._api.requestMove(this._mm, move);
	}

	/* Websocket Event Listener methods */
	handleMoveEvent(move) {
		this._mm.moveMade();
	}

	syncModelWithRemote() {
		this._api.syncMatchState(this._model);
	}

}

m = new Match(config, matchData, playerData);