function logDebug(msg, eventType) {
	if (config.debug) {
		let typeMsg = (eventType != null) ? `(${eventType} Event) ` : '';
		console.debug(`${typeMsg}${msg}`);
	}
}

// WebsocketHandler listens to events from the backend on behalf of the
// other classes.
class WebsocketHandler {

	constructor(config, connectionHash) {
		logDebug('Constructing WebsocketHandler.');
		this._connectionHash = connectionHash;
		this._conn = this._setupServerConn(config.apiRoot);
		this._registerEventListeners();
	}

	setListener(listener) {
		this._listener = listener;
	}

	_setupServerConn(url) {
		logDebug('Setting up server connection.');
		return io(url + '/match-moves');
	}

	_registerEventListeners() {
		logDebug('Registering ws event listeners.', 'Websocket');
		this._conn.on('connect', event => {
			logDebug('Connected to server.', 'Websocket');
			logDebug('Authenticating...', 'Websocket');
			this._conn.emit('authenticate', {
				token: config.token,
				connectionHash: this._connectionHash 
			});
		});
		this._conn.on('authenticated', event => {
			logDebug('Authenticated', 'Websocket');
			logDebug(event);
		});
		this._conn.on('match-begun', event => {
			logDebug('Match begun', 'Websocket');
			this._listener.handleMatchBegin(
				event.current_fen,
				event.joining_player
			);
		});
		this._conn.on('move-made', event => {
			logDebug('Move made', 'Websocket');
			console.debug(event);
			this._listener.handleMoveEvent(
				event.player,
				event.uci_string,
				event.current_fen
			);
		});
		this._conn.on('match-finish', event => {
			logDebug('Match Finished', 'Websocket');
			this._listener.handleMatchFinish(
				event.winning_player
			);
		});
	}

}


// APIHandler makes requests to the api on behalf of the other classes.
class APIHandler {

	constructor(config) {
		logDebug('Constructing APIHandler.');
		this.apiUrl = config.apiRoot;
	}

	syncMatchState(model) {
		fetch(`${window.location.href}/match/api/${model.matchId}`, {
			method: 'GET',
		}).then(response => {
			return response.json();
		}).then(json => {
			model.reload(json.current_fen);
		});
		// fetch(`${this.apiUrl}/match/${model.matchId}`, {
		// 	method: 'GET',
		// 	headers: {
		// 		'Authorization': `Bearer ${config.token}`
		// 	}
		// }).then(response => {
		// 	return response.json();
		// }).then(json => {
		// 	model.reload(json.current_fen);
		// });
	}

	requestMove(model, move) {
		logDebug('(API Event) requesting move: ' + move);
		fetch(`${window.location.origin}/match/api/${model.matchId}/make-move`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({
				uci_string: move
			})
		}).then(response => {
			return response.json();
		}).then(json => {
			logDebug('(Server Response)');
			console.debug(json);
			// Do nothing with a successful request, as it will trigger
			// a websocket event from the server. That event is then handled
			// elsewhere.
		});
	}

}

// This is just a client cache for the backend's model. Its main
// intention is to allow client-side move verification.
class MatchModel {

	constructor(matchData, playerData, opponentData = null) {
		logDebug('Constructing MatchModel.');
		this._board = new Chess();
		// console.log(matchData.history[matchData.history.length - 1]);
		if (matchData.history.length > 0) {
			this._board.load(matchData.history[matchData.history.length - 1]);
		}
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
		this._opponentId = null;
		if (this._playerSide != null) {
			this._opponentSide = this._playerSide == 'b' ? 'w' : 'b';
		}
		if (opponentData != null) {
			this._opponentId = opponentData.id;
		}
	}

	setListener(listener) {
		this._listener = listener;
	}

	loadOpponent(opponentData) {
		this._opponentId = opponentData.id;
		this._opponentSide = this._playerSide == 'b' ? 'w' : 'b';
		this._listener.renderNewOpponent(opponentData, this._opponentSide);
	}

	begin(fen) {
		this.reload(fen);
	}

	reload(fen) {
		logDebug(`(Reload Event) Match model reloading with fen: '${fen}'`)
		let successful = this._board.load(fen);
		if (successful) {
			this._listener.handleModelReload();
		} else {
			console.error(`Unable to load board from fen: ${fen}`)
		}
	}

	playersTurn(id = null) {
		if (id != null) {
			if (id == this._playerId) {
				return this._board.turn() == this._playerSide;
			} else if (this._opponentId != null && id == this._opponentId) {
				return this._board.turn() ==  this._opponentSide;
			}
			throw new RangeError(`no such player id in match: ${id}`);
		}
		if (this._playerSide == null) {
			return false;
		}
		return this._board.turn() == this._playerSide;
	}

	getPlayerId() {
		return this._playerId;
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

	// Note this assumes that this move is being requested by the player, not
	// the opponent.
	promotionAvailable(move) {
		let from = move.substring(0, 2);
		let to = move.substring(2, 4);
		if (this.pieceAt(from).type != 'p') {
			return false;
		}
		let promoRank = (this.playerSide == 'b') ? '1' : '8';
		return (to[1] === promoRank);
	}

	movesFrom(fromSquare) {
		return this._board.moves({
			verbose: true
		}).filter(move => move.from == fromSquare);
	}

	moveMade(player, uciString, currentFen) {
		this.reload(currentFen);
	}

}


// Like the class name implies, this controls the board view. It
// handles all player actions.
class BoardViewController {

	constructor(model) {
		logDebug('Constructing BoardViewController.');
		this._pieceNames = {
			p: 'pawn', r: 'rook', n: 'knight',
			b: 'bishop', k: 'king', q: 'queen'
		}
		this._setupClickHandlers();
		this._model = model;
		this._model.setListener(this);
		this._selectedSquare = null;
		this._moveBuffer = null;
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
		let promoButton = document.getElementById('promotion-button');
		// This should only be visible when promotion is an option, but could
		// perhaps be made more secure with some kind of status check. Also
		// This is difficult to program for latency/server failure.
		promoButton.addEventListener('click', event => {
			let promos = document.getElementsByName('promo-choices');
			for (const promo of promos) {
				if (promo.checked) {
					logDebug(`promotion selected: ${promo.value}, requesting move.`, 'Render')
					let move = this._moveBuffer;
					this._moveBuffer = null;
					this._listener.handleMoveRequest(move + promo.value);
					document.getElementById('promotion-choices').classList.add('hidden');
				}
			}
		});
	}

	_renderMoveOptions(fromSquare) {
		logDebug('Rendering move options', 'Render');
		this._selectedSquare = fromSquare;
		document.getElementById(fromSquare).classList.add('selected-square');
		for (const move of this._model.movesFrom(fromSquare)) {
			logDebug('(Render Event) rendering move option: ' + fromSquare + move.to);
			document.getElementById(move.to).classList.add('move-option');
		}
	}

	_clearRenderedMoveOptions() {
		logDebug('Clearing rendered move options', 'Render');
		if (this._selectedSquare != null) {
			document.getElementById(this._selectedSquare).classList.remove('selected-square');
			this._selectedSquare = null;
		}
		let options = document.querySelectorAll('.board-square.move-option');
		for (const option of options) {
			logDebug(`Clearing 'move-option' from square: ${option.id}`, 'Render');
			option.classList.remove('move-option');
		}
	}

	_handleSquareClick(event) {
		let square = event.currentTarget;
		if (config.debug) {
			let pieceJSON = JSON.stringify(this._model.pieceAt(square.id));
			logDebug(`Piece at ${square.id} ${pieceJSON}`, 'Click');
		}
		if (this._model.playersTurn() && this._moveBuffer == null) {
			if (square.classList.contains('move-option')) {
				let move = this._selectedSquare + square.id;
				if (this._model.promotionAvailable(move)) {
					logDebug(`Promotion available, buffering move: ${move}`, 'Render')
					this._moveBuffer = move;
					this._displayPromotionChoices()
				} else {
					this._listener.handleMoveRequest(move);
				}
			} else if (this._selectedSquare != null) {
				this._clearRenderedMoveOptions();
			} else if (this._model.playersPiece(square.id)) {
				this._renderMoveOptions(square.id);
			}
		}
	}

	_displayPromotionChoices(side) {
		if (config.debug) {
			logDebug('Displaying promotion options', 'Render');
		}
		let choicesEl = document.getElementById('promotion-choices');
		choicesEl.classList.remove('hidden');
	}

	// Probably faster to inline this up top but this is a lot cleaner.
	_renderPieceIconHTML(side, piece) {
		let weight = (side == 'b') ? 's' : 'l';
		return `
			<i class="fa${weight} fa-chess-${this._pieceNames[piece]} piece"></i>
		`
	}

	_renderPieceIconElement(side, piece) {
		let weight = (side == 'b') ? 's' : 'l';
		let ret = document.createElement('<i></i>');
		ret.classList.add(
			`fa${weight}`, `fa-chess-${this._pieceNames[piece]}`, 'piece'
		);
		return ret;
	}

	_render() {
		// render board
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
		// render players
		// if (this._model.playersTurn()) {
		// 	let turnIcon = document.getElementById(
		// 		`player-${this._model.getPlayerId()}`
		// 	);

		// }
	}

	_renderPlayerHTML(playerData, playerSide) {
		let side = (playerSide == 'w') ? 'white' : 'black';
		let playersTurn = '';
		if (this._model.playersTurn(playerData.id)) {
			playersTurn == '<i class="far fa-chevron-double-left"></i>'
		}
		return `
			<h3
				id="player-${playerData.id}"
				class="player-title player-${side}-title"
			>${playerData.username}</h3>${playersTurn}
		`
	}

	renderNewOpponent(opponentData, opponentSide) {
		let side = (opponentSide == 'w') ? 'white' : 'black'; 
		let container = document.getElementById(`player-${side}`);
		container.innerHTML = this._renderPlayerHTML(
			opponentData,
			opponentSide
		);
	}

	handleGameOver(winner) {
		let winnerEl = document.getElementById(`player-${winner.id}`);
		winnerEl.innerText = winnerEl.innerText + ' Winner!';
		document.getElementById('board').classList.add('game-over');
	}

	/* ModelListener methods */
	handleModelReload() {
		this._moveBuffer = null;
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
		this._wsh = new WebsocketHandler(config, matchData.connection_hash);
		this._wsh.setListener(this);
	}

	static parseDOMMatchData() {
		let matchDataEl = document.getElementById('match-data');
		return JSON.parse(matchDataEl.dataset.matchData);
	}

	static parseDOMPlayerData() {
		let playerDataEl = document.getElementById('player-data');
		return JSON.parse(playerDataEl.dataset.playerData);
	}

	/* Board View Controller Listener methods */
	handleMoveRequest(move) {
		this._api.requestMove(this._mm, move);
	}

	/* Websocket Event Listener methods */
	handleMatchBegin(currentFen, joiningPlayer) {
		this._mm.loadOpponent(joiningPlayer)
		this._mm.begin(currentFen);
	}

	handleMoveEvent(playerJSON, uciString, currentFen) {
		this._mm.moveMade(playerJSON, uciString, currentFen);
	}

	handleMatchFinish(winningPlayerJSON) {
		this._bvc.handleGameOver(winningPlayerJSON);
	}

	syncModelWithRemote() {
		this._api.syncMatchState(this._model);
	}

}

let m = new Match(
	config,
	Match.parseDOMMatchData(),
	Match.parseDOMPlayerData()
);