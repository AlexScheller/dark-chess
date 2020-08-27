/* Utility Functions */

function logDebug(msg, eventType = null) {
	if (config.debug) {
		let typeMsg = (eventType != null) ? `(${eventType} Event) ` : '';
		console.debug(`${typeMsg}${msg}`);
	}
}

function swapEl(el1, el2) {
	let tempLoc = document.createElement('div');
	el1.parentNode.insertBefore(tempLoc, el1);
	el2.parentNode.insertBefore(el1, el2);
	tempLoc.parentNode.insertBefore(el2, tempLoc)
	tempLoc.parentNode.removeChild(tempLoc);
}

// WebsocketHandler listens to events from the backend on behalf of the other
// classes. Since we don't want to leak player positions, most of these simply
// prompt the API handler to request a new model state.
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
		this._conn.on('match-begun', () => {
			logDebug('Match begun', 'Websocket');
			this._listener.handleMatchBegin();
		});
		this._conn.on('move-made', event => {
			logDebug('Move made', 'Websocket');
			if (config.debug) {
				console.debug(event);
			}
			this._listener.handleMoveEvent();
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
		fetch(`${window.location.origin}/match/api/${model.matchId}`, {
			method: 'GET',
		}).then(response => {
			if (!response.ok) {
				if (response.status == 401) {
					utilities.handleProxyUnauthorized();
				} else {
					throw Error (response.statusText);
				}
			} else {
				return response.json();
			}
		}).then(json => {
			model.reload(json);
		});
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
			if (!response.ok) {
				if (response.status == 401) {
					utilities.handleProxyUnauthorized();
				} else {
					throw Error (response.statusText);
				}
			} else {
				return response.json();
			}
		}).then(json => {
			logDebug('(Server Response)');
			if (config.debug) {
				console.debug(json);
			}
			// Do nothing with a successful request, as it will trigger
			// a websocket event from the server. That event is then handled
			// elsewhere.
		});
	}

}

class MatchModel {

	constructor(matchData, playerData, opponentData = null) {
		logDebug('Constructing MatchModel.');
		this._matchData = matchData;
		console.log(matchData);
		if (this._matchData.in_progress) {
			this._board = this.loadFromDarkFen(this._matchData.current_dark_fen);
		}
		this._playerData = playerData;
		this._opponentData = opponentData;
	}

	reload(matchData) {
		logDebug('(Load Event) loading/reloading match model.');
		this._matchData = matchData;
		if (matchData.in_progress) {
			this._board = this.loadFromDarkFen(matchData.current_dark_fen);
			if (this._playerData.id == matchData.player_black.id) {
				this._opponentData = matchData.player_white;
			} else {
				this._opponentData = matchData.player_black;
			}
		}
		this._listener.handleModelReload();
	}

	// Public accessors for internal data clusters.
	
	// Many of these could be made
	// more performant by a one time check at instantiation-time, but a client
	// will only run a single one of these match models at once, and for now I
	// prefer the functional approach.

	get matchId() {
		return this._matchData.id;
	}

	get playerSide() {
		if (this._matchData.player_black?.id == this._playerData.id) return 'b';
		if (this._matchData.player_white?.id == this._playerData.id) return 'w';
		return null;
	}

	get opponentSide() {
		if (this.playerSide) {
			return this.playerSide == 'w' ? 'b' : 'w';
		}
		return null;
	}

	get inProgress() {
		return this._matchData.in_progress;
	}

	get turn() {
		if (this._matchData.in_progress) {
			return this._matchData.current_side == 'white' ? 'w' : 'b';
		}
		return null;
	}

		// This seems pretty jank...
	contentAtSquare(square) {
		if (this._board) {
			let value = this._board[square].toLowerCase();
			let type = ['_', '?'].includes(value) ? 'vision' : 'piece';
			let color = null;
			if (type === 'piece') {
				// If the piece were originally lower case, it is black.
				color = this._board[square] === value ? 'b' : 'w'; 
			}
			return { type, value, color }
		}
		return null;
	}

	pieceAtSquare(square) {
		if (this._board) {
			let content = this.contentAtSquare(square);
			if (content.type !== 'piece') {
				return null;
			}
			return { type: content.value, color: content.color };
		}
		return null;
	}

	playersTurn(id = null) {
		if (id != null) {
			if (id == this._playerData.id) {
				return this.turn == this.playerSide;
			} else if (this._opponentData?.id == id) {
				return this.turn == this.opponentSide;
			}
			throw new RangeError(`no such player id in match: ${id}`);
		}
		if (this.playerSide == null) {
			return false;
		}
		return this.turn == this.playerSide;
	}

	playersPiece(square) {
		let squarePiece = this.pieceAtSquare(square);
		if (squarePiece == null || this.playerSide == null) {
			return null;
		}
		return this.playerSide == squarePiece.color;
	}

	movesFrom(fromSquare) {
		let ret = this._matchData?.possible_moves[fromSquare];
		return ret !== undefined ? ret : [];
	}

	moveMade(player, uciString, currentFen) {
		this.reload(currentFen);
	}

	setListener(listener) {
		this._listener = listener;
	}

	loadFromDarkFen(darkFen) {
		let ret = {}
		let squares = darkFen.split('/').join('')
		let curr = 0;
		for (let rank of '87654321') {
			for (let file of 'abcdefgh') {
				ret[file + rank] = squares[curr++] 
			}
		}
		return ret;
	}

	loadOpponent(opponentData) {
		this._opponentData = opponentData;
		this._listener.renderNewOpponent(opponentData, this.opponentSide);
	}

	// reload(darkFen, possibleMoves = null) {
	// 	logDebug(`(Reload Event) Match model reloading with fen: '${darkFen}'`);
	// 	this._board = this.loadFromDarkFen(darkFen);
	// 	this._possibleMoves = possibleMoves;
	// 	this._listener.handleModelReload();
	// }

	// reloadMatchState(matchData) {
	// 	logDebug(`(Reload Event) Match model reloading.`);
	// 	this._board = this.loadFromDarkFen(matchData.current_dark_fen);
	// 	this._possibleMoves = matchData.possible_moves;
	// 	this._listener.handleModelReload();
	// }

	begin(matchData) {
		this.reload(matchData);
	}

}

// Like the class name implies, this controls the board view. It handles all
// player actions. This implementation relies on the Canvas API.
class CanvasBoardViewController {

	constructor(model, squareWidth = 60) {
		logDebug('Constructing CanvasBoardViewController.');
		this._canvas = document.getElementById('board-canvas');
		if (this._canvas.getContext) {
			
			this._model = model;
			this._active = this._model.inProgress;
			this._model.setListener(this);

			this._squareWidth = squareWidth;
			
			this._canvas.height = this._height;
			this._canvas.width = this._height;

			this._ctx = this._canvas.getContext('2d');

			this._moveOptions = [];
			this._selectedSquare = null;

			this._boardFlipped = false;

			if (this._model.playerSide === 'b') {
				this._flipBoard();
			}

			if (this._active) {
				this._setupClickHandlers();
			}

			this._render();
		} else {
			this._canvas.classList.add('disabled');
			throw new Error('Canvas API not supported.')
		}
	}

	/* Setup */

	setListener(listener) {
		this._listener = listener;
	}

	/* event handlers */

	_setupClickHandlers() {
		this._canvas.addEventListener('click', event => {
			this._handleSquareClick(event);
		});
		let flipBoardButton = document.getElementById('flip-board-button');
		flipBoardButton.addEventListener('click', event => {
			this._handleFlipBoardClick();
		});
	}

	_handleFlipBoardClick() {
		this._flipBoard();
	}

	_handleSquareClick(event) {
		if (this._active) {
			let point = {x: event.offsetX, y: event.offsetY};
			let square = this._pointToSquare(point);
			if (config.debug) {
				let piece = this._model.pieceAtSquare(square);
				if (piece != null) {
					let pieceJSON = JSON.stringify(piece);
					logDebug(`Piece at ${square} ${pieceJSON}.`, 'Click');
				} else {
					logDebug(`Square at ${square}.`, 'Click');
				}
			}
			if (this._model.playersTurn()) {
				if (
					this._model.playersPiece(square) &&
					this._selectedSquare !== square // otherwise clear options.
				) {
					this._clearMoveOptions();
					this._fillMoveOptions(square);
				} else if (this._moveOptions.includes(square)) {
					let move = this._selectedSquare + square;
					this._listener.handleMoveRequest(move);
				} else {
					this._clearMoveOptions();
				}
				this._render();
			}
			// if (this._model.playersTurn() && this._moveBuffer == null) {
			// 	if (square.classList.contains('move-option')) {
			// 		let move = this._selectedSquare + square.id;
			// 		if (this._model.promotionAvailable(move)) {
			// 			logDebug(`Promotion available, buffering move: ${move}`, 'Render')
			// 			this._moveBuffer = move;
			// 			this._displayPromotionChoices()
			// 		} else {
			// 			this._listener.handleMoveRequest(move);
			// 		}
			// 	} else if (this._selectedSquare != null) {
			// 		this._clearRenderedMoveOptions();
			// 	} else if (this._model.playersPiece(square.id)) {
			// 		this._renderMoveOptions(square.id);
			// 	}
			// }
		}
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

	/* ModelListener methods */
	renderNewOpponent(opponentData, opponentSide) {
		let side = (opponentSide == 'w') ? 'white' : 'black'; 
		let container = document.getElementById(`player-${side}`);
		container.innerHTML = this._renderPlayerHTML(
			opponentData,
			opponentSide
		);
	}

	handleModelReload() {
		this._selectedSquare = null;
		this._clearMoveOptions();
		this._active = this._model.inProgress;
		this._render();
	}

	// handleGameOver(winner) {
	// 	// flash the checkmated king
	// 	let interval = 1000;
	// 	let expectedTick = Date.now() + interval;
	// 	function tick() {
	// 		let drift = Date.now() - expectedTick;
	// 		if (drift > interval) {
	// 			// TODO: do something?
	// 		}
	// 		// flash/render
	// 		expectedTick += interval;
	// 		setTimeout(tick(), Math.max(0, interval - drift));
	// 	}
	// 	tick();
	// }

	/* internals */

	get _height() {
		return this._squareWidth * 8;
	}

	get _width() {
		return this._squareWidth * 8;
	}

	get _lineWidth() {
		let ret = Math.floor(this._squareWidth / 30);
		return ret > 0 ? ret : 1;
	}

	_pointToSquare(point) {
		let ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];
		let files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
		if (this._boardFlipped) {
			ranks.reverse();
			files.reverse();
		}
		let rank = ranks[Math.floor(point.y / this._squareWidth)];
		let file = files[Math.floor(point.x / this._squareWidth)];
		let origin = this._squareToOrigin(file + rank);
		return file + rank;
	}

	_squareToOrigin(square) {
		let ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];
		let files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
		if (this._boardFlipped) {
			ranks.reverse();
			files.reverse();
		}
		let x = files.indexOf(square[0]) * this._squareWidth;
		let y = ranks.indexOf(square[1]) * this._squareWidth;
		return {x, y};
	}

	_clearMoveOptions() {
		logDebug('Clearing move options', 'Render');
		this._selectedSquare = null;
		this._moveOptions = [];
	}

	_fillMoveOptions(fromSquare) {
		logDebug('Filling move options', 'Render');
		this._selectedSquare = fromSquare;
		for (const move of this._model.movesFrom(fromSquare)) {
			logDebug(`move option: ${fromSquare} to ${move}`, 'Render');
			this._moveOptions.push(move);
		}
	}

	_flipBoard() {
		// There are still a few things that are handled with regular old html
		// elements.
		let playerWhite = document.getElementById('player-white'); 
		let playerBlack = document.getElementById('player-black');
		swapEl(playerWhite, playerBlack);
		// The rest is handled on the canvas
		this._boardFlipped = !this._boardFlipped;
		this._render();
	}

	/* helper canvas methods */
	
	_helperDrawLine(p1, p2) {
		this._ctx.beginPath();
		this._ctx.moveTo(p1.x, p1.y);
		this._ctx.lineTo(p2.x, p2.y);
		this._ctx.closePath();
		this._ctx.stroke();
	}

	_helperHighlightSquare(square, color) {
		let resetStyle = this._ctx.strokeStyle;
		let origin = this._squareToOrigin(square);
		this._ctx.strokeStyle = color;
		this._ctx.strokeRect(
			origin.x + 2,
			origin.y + 2,
			this._squareWidth - 4,
			this._squareWidth - 4
		)
		this._ctx.strokeStyle = resetStyle;
	}

	/* Core Rendering */

	/* Piece rendering */

	_drawPiece(piece, origin) {
		let center = {
			x: origin.x + Math.floor(this._squareWidth / 2),
			y: origin.y + Math.floor(this._squareWidth / 2)
		}
		this._ctx.fillStyle = 'black';
		if (piece.type === 'p') { // pawns
			let rad = Math.floor(this._squareWidth / 4);
			this._ctx.beginPath();
			this._ctx.arc(center.x, center.y, rad, 0, Math.PI * 2);
			if (piece.color === 'b') {
				this._ctx.fill();
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.stroke();
			}
		} else if (piece.type === 'n') { // knights
			this._ctx.beginPath();
			// left ear
			this._ctx.moveTo(
				center.x - (this._squareWidth / 4),
				center.y - (this._squareWidth / 3)
			);
			// central crevice
			this._ctx.lineTo(
				center.x, center.y - (this._squareWidth / 6)
			)
			// right ear
			this._ctx.lineTo(
				center.x + (this._squareWidth / 4),
				center.y - (this._squareWidth / 3)
			);
			// right eye
			this._ctx.lineTo(
				center.x + (this._squareWidth / 4),
				center.y,
			);
			// right mouth
			this._ctx.lineTo(
				center.x + (this._squareWidth / 8),
				center.y + (this._squareWidth / 3)
			);
			// left mouth
			this._ctx.lineTo(
				center.x - (this._squareWidth / 8),
				center.y + (this._squareWidth / 3)
			);
			// left eye
			this._ctx.lineTo(
				center.x - (this._squareWidth / 4),
				center.y,
			);
			if (piece.color === 'b') {
				this._ctx.fill();
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.closePath();
				this._ctx.stroke();
			}
		} else if (piece.type === 'r') { // rooks
			let length = this._squareWidth / 3;
			let height = length * 2;
			if (piece.color === 'b') {
				this._ctx.fillRect(
					center.x - (length / 2),
					center.y - (height / 2),
					length,
					height
				);
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.strokeRect(
					center.x - (length / 2),
					center.y - (height / 2),
					length,
					height
				);
			}
		} else if (piece.type === 'b') { // bishops
			this._ctx.beginPath();
			this._ctx.moveTo(
				center.x,
				center.y - (this._squareWidth / 3)
			);
			this._ctx.lineTo(
				center.x + (this._squareWidth / 4),
				center.y + (this._squareWidth / 3)
			);
			this._ctx.lineTo(
				center.x - (this._squareWidth / 4),
				center.y + (this._squareWidth / 3)
			);
			if (piece.color === 'b') {
				this._ctx.fill();
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.closePath();
				this._ctx.stroke();
			}
		} else if (piece.type === 'k') { // kings
			this._ctx.beginPath();
			// left spike
			this._ctx.moveTo(
				center.x - (this._squareWidth / 3),
				center.y - (this._squareWidth / 3),
			);
			// central crevice
			this._ctx.lineTo(center.x, center.y);
			// right spike
			this._ctx.lineTo(
				center.x + (this._squareWidth / 3),
				center.y - (this._squareWidth / 3),
			);
			// right base
			this._ctx.lineTo(
				center.x + (this._squareWidth / 3),
				center.y + (this._squareWidth / 3)
			);
			// left base
			this._ctx.lineTo(
				center.x - (this._squareWidth / 3),
				center.y + (this._squareWidth / 3)
			);
			if (this._model.turn == piece.color) {
				this._ctx.strokeStyle = 'red';
				this._ctx.fillStyle = 'red';
			}
			if (piece.color === 'b') {
				this._ctx.fill();
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.closePath();
				this._ctx.stroke();
			}
			// jewel
			this._ctx.beginPath();
			this._ctx.arc(
				center.x,
				center.y - (this._squareWidth / 4),
				Math.floor(this._squareWidth / 8),
				0,
				Math.PI * 2
			);
			if (piece.color === 'b') {
				this._ctx.fill();
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.stroke();
			}
			this._ctx.strokeStyle = 'black';
			this._ctx.fillStyle = 'black';
		} else if (piece.type === 'q') { // queens
			this._ctx.beginPath();
			// left spike
			this._ctx.moveTo(
				center.x - (this._squareWidth / 3),
				center.y - (this._squareWidth / 8),
			);
			// left crevice
			this._ctx.lineTo(
				center.x - (this._squareWidth / 6),
				center.y
			);
			// central spike
			this._ctx.lineTo(
				center.x,
				center.y - (this._squareWidth / 3),
			);
			// right crevice
			this._ctx.lineTo(
				center.x + (this._squareWidth / 6),
				center.y
			);
			// right spike
			this._ctx.lineTo(
				center.x + (this._squareWidth / 3),
				center.y - (this._squareWidth / 8)
			);
			// right base
			this._ctx.lineTo(
				center.x + (this._squareWidth / 4),
				center.y + (this._squareWidth / 3)
			);
			// left base
			this._ctx.lineTo(
				center.x - (this._squareWidth / 4),
				center.y + (this._squareWidth / 3)
			)
			if (piece.color === 'b') {
				this._ctx.fill();
			} else {
				this._ctx.lineWidth = this._lineWidth;
				this._ctx.closePath();
				this._ctx.stroke();
			}
		} else {
			throw Error(`No drawing handler for piece of type: ${piece.type}`)
		}

	}

	_drawFog(origin) {
		let center = {
			x: origin.x + Math.floor(this._squareWidth / 2),
			y: origin.y + Math.floor(this._squareWidth / 2)
		}
		this._ctx.fillStyle = 'black';
		let crossHalfWidth = this._squareWidth / 2;
		this._ctx.lineWidth = this._lineWidth;
		this._helperDrawLine(
			{ x: center.x - crossHalfWidth, y: center.y - crossHalfWidth },
			{ x: center.x + crossHalfWidth, y: center.y + crossHalfWidth }
		);
		this._helperDrawLine(
			{ x: center.x + crossHalfWidth, y: center.y - crossHalfWidth },
			{ x: center.x - crossHalfWidth, y: center.y + crossHalfWidth }
		);
	}

	_render() {
		// clear the canvas
		this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
		// render grid
		for (let row = 0; row < 10; row++) {
			this._helperDrawLine(
				{x: 0, y: this._squareWidth * row},
				{x: this._width, y: this._squareWidth * row}
			);
		}
		for (let col = 0; col < 10; col++) {
			this._helperDrawLine(
				{x: this._squareWidth * col, y: 0},
				{x: this._squareWidth * col, y: this._width}
			);
		}
		// render filled in squares
		this._ctx.fillStyle = '#6aa1c8';
		for (let row = 0; row < 9; row++) {
			let offset = row % 2 == 1 ? 0 : 1;
			for (let col = 0; col < 4; col++) {
				let unspacedX = col * this._squareWidth + 1;
				let spacedX = unspacedX + ((col + offset) * this._squareWidth);
				let xOrigin = spacedX;
				this._ctx.fillRect(
					xOrigin,
					(row * this._squareWidth) + 1,
					this._squareWidth - 2,
					this._squareWidth - 2
				);
			}
		}
		// render pieces
		for (let rank = 1; rank <= 8; rank++) {
			for (let file of 'abcdefgh') {
				let squareContent = this._model.contentAtSquare(file + rank);
				if (squareContent != null) {
					let origin = this._squareToOrigin(file + rank);
					if (squareContent.type === 'piece') {
						let piece = {
							type: squareContent.value,
							color: squareContent.color 
						};
						this._drawPiece(piece, origin);
					} else if (
						squareContent.type === 'vision' &&
						squareContent.value == '?'
					) {
						this._drawFog(origin)
					}
				}
			}
		}
		// render selected square and move options
		if (this._selectedSquare != null) {
			this._helperHighlightSquare(this._selectedSquare, 'blue');			
		}
		for (const square of this._moveOptions) {
			this._helperHighlightSquare(square, 'green');
		}
	}

}


// Like the class name implies, this controls the board view. It
// handles all player actions. This implementation relies on maniuplating
// HTML Elements for displaying the board and handling input.
//
// As of 2020-05-31, this Controller is deprecated, but kept in the source for
// posterity, in case it ever gets revived.
class HTMLElementBoardViewController {

	constructor(model) {
		logDebug('Constructing HTMLElementBoardViewController.');
		this._pieceNames = {
			p: 'pawn', r: 'rook', n: 'knight',
			b: 'bishop', k: 'king', q: 'queen'
		}
		this._setupClickHandlers();
		this._model = model;
		this._model.setListener(this);
		this._selectedSquare = null;
		this._moveBuffer = null;
		this._boardEl = document.getElementById('board');
		this._boardEl.classList.remove('disabled');
		if (this._model.playerSide == 'b') {
			this._flipBoard();
		}
		this._render();
	}

	/* Setup */

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
		let flipBoardButton = document.getElementById('flip-board-button');
		flipBoardButton.addEventListener('click', event => {
			this._handleFlipBoardClick();
		});
	}

	/* Input Handlers */

	_handleSquareClick(event) {
		let square = event.currentTarget;
		if (config.debug) {
			let pieceJSON = JSON.stringify(this._model.pieceAtSquare(square.id));
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

	_handleFlipBoardClick(event) {
		this._flipBoard();
	}

	/* Core Rendering */

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

	// When playing as black
	_flipBoard() {
		for (const col of 'abcdefgh') {
			for (let row = 1; row <= 4; row++) {
				swapEl(
					document.getElementById(col + row),
					document.getElementById(col + (8 - (row - 1)))
				)
			}
		}
	}

	_render() {
		// render board
		for (let row = 1; row <= 8; row++) {
			for (const col of 'abcdefgh') {
				let piece = this._model.pieceAtSquare(col + row);
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

	/* ModelListener methods */
	renderNewOpponent(opponentData, opponentSide) {
		let side = (opponentSide == 'w') ? 'white' : 'black'; 
		let container = document.getElementById(`player-${side}`);
		container.innerHTML = this._renderPlayerHTML(
			opponentData,
			opponentSide
		);
	}

	handleModelReload() {
		this._moveBuffer = null;
		this._clearRenderedMoveOptions();
		this._render();
	}

	handleGameOver(winner) {
		let winnerEl = document.getElementById(`player-${winner.id}`);
		winnerEl.innerText = winnerEl.innerText + ' Winner!';
		document.getElementById('board').classList.add('inactive');
	}

}

// Main class
class Match {
	
	constructor(config, matchData, playerData) {
		this._mm = new MatchModel(matchData, playerData);
		// As of 2020-05-31, the HTMLElement board controllers is dprecated. If
		// The client doesn't have a browser that supports HTML5 canvas (which
		// is less than 2% of users according to caniuse.com), they simply won't
		// be able to play. The following code is kept for posterity in case
		// someone want's to revive it later.
		// try {
		// 	this._bvc = new CanvasBoardViewController(this._mm);		
		// } catch(error) {
		// 	logDebug(error);
		// 	let canvas = document.getElementById('board-canvas');
		// 	canvas.classList.add('disabled');
		// 	// fallback
		// 	this._bvc = new HTMLElementBoardViewController(this._mm);		
		// }
		this._bvc = new CanvasBoardViewController(this._mm);
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
	handleMatchBegin() {
		this.syncModelWithRemote();
	}

	handleMoveEvent() {
		this.syncModelWithRemote();
	}

	handleMatchFinish(winningPlayerJSON) {
		this._bvc.handleGameOver(winningPlayerJSON);
	}

	syncModelWithRemote() {
		this._api.syncMatchState(this._mm);
	}

}

let m = new Match(
	config,
	Match.parseDOMMatchData(),
	Match.parseDOMPlayerData()
);