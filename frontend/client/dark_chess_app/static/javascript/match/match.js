/*
	THE CANONICAL BOARD IN ALL CAPS BECAUSE YOU KEEP FORGETTING OR CHANGING YOUR
	MIND ABOUT IT IS THIS:

	8  rnbqkbnr
	7  pppppppp
	6  ________
	5  ________
	4  ________
	3  ________
	2  PPPPPPPP
	1  RNBQKBNR

	   abcdefgh

	With alternative light and dark squares, anything else is a rotation. 

*/



// TODO, convert instances of move that are represented by a string, to
// a standardized object, so that wherever "move" is referenced, it is
// understood what it is (maybe try typescript or something).

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

	constructor(config, connectionToken) {
		logDebug('Constructing WebsocketHandler.', 'Websocket');
		this._connectionToken = connectionToken;
		this._conn = this._setupServerConn(config.apiRoot);
		this._registerEventListeners();
	}

	setListener(listener) {
		this._listener = listener;
	}

	_setupServerConn(url) {
		logDebug('Setting up server connection.', 'Websocket');
		return io(url + '/match-moves');
	}

	_registerEventListeners() {
		logDebug('Registering ws event listeners.', 'Websocket');
		this._conn.on('connect', event => {
			logDebug('Connected to server.', 'Websocket');
			logDebug('Authenticating...', 'Websocket');
			this._conn.emit('authenticate', {
				token: config.token,
				connectionToken: this._connectionToken 
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
			this._listener.handleMoveEvent(event);
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
		logDebug('Constructing APIHandler.', 'API');
		this.apiUrl = config.apiRoot;
	}

	syncMatchState(model) {
		logDebug('Requesting Match State', 'API Request')
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
		console.debug(matchData);
		if (this._matchData.in_progress) {
			// For testing fog of war.
			// this._board = this.loadFromDarkFen('r_b_k_nr/p__p_p?p/n_???_?_/_p_?P???/__?_????/_?_?_???/__???_?_/q_____b?');
			this._board = this.loadFromDarkFen(this._matchData.current_dark_fen);
		}
		this._playerData = playerData;
		this._opponentData = opponentData;
		this._promoMoveBuffer = null;
		this._latestMove = null;
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
		} else {
			this._board = this.loadFromFen(matchData.current_fen);
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

	get promotionMove() {
		return this._promoMoveBuffer;
	}

	get promoting() {
		return this._promoMoveBuffer !== null;
	}

	// Note that this assumes the requesting method only requests when it's the
	// player's turn...It could really use some checks.
	potentialPromotion(move) {
		logDebug('Checking potential promotion', 'Game');
		let piece = this.pieceAtSquare(move.from);
		let capture = this.pieceAtSquare(move.to);
		if (piece === null) return false;
		if (capture !== null) {
			// If it's capturing the king the pawn shouldn't promote.
			if (capture.color === this.opponentSide && capture.type === 'k') {
				return false;
			}
		}
		if (piece.color === this.playerSide && piece.type === 'p') {
			let rank = move.to[1];
			return piece.color === 'w' ? rank === '8' : rank === '1';
		}
		return false
	}

	// This is to handle the edge case where a pawn is capturing a king on the
	// backline. In our varient, this ends the game so a promtion shouldn't be
	// strictly necessary, but the chess library on the backend doesn't
	// currently consider this to be a pseudo-legal move. If this returns true,
	// the caller will append a filler queen promotion to the end of the move to
	// make the library happy. If the libary is updated this should be removed.
	// NOTE that this will result in the pawn promoting to a queen. If that's
	// not desired it will have to be fixed on the backend.
	pawnCaptureKingPromotion(move) {
		logDebug('Checking potential pawn capturing king', 'Game');
		let piece = this.pieceAtSquare(move.from);
		let capture = this.pieceAtSquare(move.to);
		if (piece === null) return false;
		if (piece.color === this.playerSide && piece.type === 'p') {
			let rank = move.to[1];
			return piece.color === 'w' ? rank === '8' : rank === '1';
		}
		return false
	}

	// TODO: Rework/Refactor how promotions are handled.
	bufferPromotion(move) {
		this._promoMoveBuffer = move;
	}

	clearPromotion() {
		this._promoMoveBuffer = null;
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

	// Currently, there's no difference in board loading between dark and
	// regular fen. That may not always be the case however, so seperate
	// functions are kept in case it changes. Until then, both functions simply
	// call this helper function.
	_loadFen(fen) {
		let ret = {};
		let squares = fen.split('/').join('');
		let curr = 0;
		for (let rank of '87654321') {
			for (let file of 'abcdefgh') {
				ret[file + rank] = squares[curr++];
			}
		}
		return ret;
	}

	// Used when playing the game.
	loadFromDarkFen(darkFen) {
		return this._loadFen(darkFen);
	}

	// Used when spectating an in progress game, or displaying a finished game.
	loadFromFen(fen) {
		return this._loadFen(fen);
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

class KonvaBoardViewController {

	constructor(model, options = {}) {

		logDebug('Creating KonvaBoardViewController', 'ViewController');

		let defaults = {
			containerId: 'board',
			squareSize: 64,
			darkSquareColor: '#6aa1c8',
			lightSquareColor: 'white',
			pieceColor: 'black',
			playersTurnColor: 'red', // '#d64933',
			fogColor: 'black',
			fogOpacity: 0.6,
			infoObjectColor: '#ff6b35',
			infoObjectOpacity: 1,
			animationSpeed: 1 // seconds
		};
		this._config = Object.assign(defaults, options);

		this._dimensions = {
			squareSize: this._config.squareSize,
			boardHeight: this._config.squareSize * 8,
			boardWidth: this._config.squareSize * 8,
		}

		this._model = model;
		this._model.setListener(this);

		/*** Konva OBject References ***/

		// Used for remembering where the pieces are in terms of ranks and
		// files. The Konva piece objects track their actual visual location,
		// but we also need a reference for the board in order to more easily
		// diff the current visual state with a new board state for animation
		// purposes. It's basically the same as the board buffer in the model,
		// but only due to convergent evolution.
		this._boardBuffer = new Map();
		// Unlike the board buffer where we want to search for pieces, we don't
		// care where the fog is, we just need a reachable reference to it.
		this._fog = [];
		// same with move options
		this._moveOptions = [];
		this._highlightedSquares = [];
		this._opponentSquareHighlight = null;

		this._boardFlipped = false;
		if (this._model.playerSide === 'b') {
			this._flipBoard();
		}

		this._setupClickHandlers();

		this._stage = new Konva.Stage({
			container: this._config.containerId,
			width: this._dimensions.boardWidth,
			height: this._dimensions.boardHeight
		});
		// For rendering the underlying board.
		this._boardLayer = this._setupBoardLayer();
		// For rendering the fog of war.
		this._fogLayer = this._setupFogLayer();
		// For rendering things like the rank and file labels, as well as
		// planning arrows and such.
		this._infoOverlayLayer = this._setupInfoOverlayLayer();
		// For rendering the pieces and fog of war.
		this._pieceLayer = this._setupPieceLayer();
		// For rendering promotions. Only active while accepting a promotion
		// choice.
		this._promotionLayer = null;

		this._stage.add(this._boardLayer);
		this._stage.add(this._fogLayer);
		this._stage.add(this._infoOverlayLayer);
		this._stage.add(this._pieceLayer);

		this._render();
	}

	/*** Derivables ***/
	
	// This is currently redundant, but will not be in the future.
	get _active() {
		return this._matchActive;
	}

	get _matchActive() {
		return this._model.inProgress;
	}

	/*** Setup ***/

	setListener(listener) {
		this._listener = listener;
	}

	_setupBoardLayer() {
		logDebug('Setting up board layer', 'ViewController');
		let ret = new Konva.Layer();
		let alternationTest = this._boardFlipped ? 0 : 1;
		for (let rank = 0; rank < 8; rank++) {
			for (let file = 0; file < 8; file++) {
				// Dark squares of course occur every other square, alternating'
				// beginnings based on rank.
				let darkFill = (rank % 2 == alternationTest) ? (file % 2 == 1) : (file % 2 == 0);
				ret.add(
					new Konva.Rect({
						x: file * this._dimensions.squareSize,
						y: rank * this._dimensions.squareSize,
						width: this._dimensions.squareSize,
						height: this._dimensions.squareSize,
						fill: darkFill ? this._config.darkSquareColor :
										 this._config.lightSquareColor
					})
				);
			}
		}
		return ret;
	}

	// Note that the fog layer and piece layers technically iterate over the
	// same content, and could thus be created at the same time (in fact, they
	// used to be a part of the same layer), but this efficiency isn't worth the
	// understandability/refactorability of having them be two seperate loops.
	// Either way it's constant time (unless the chessboard becomes variable in
	// size).
	_setupFogLayer() {
		logDebug('Setting up fog layer', 'ViewController');
		let ret = new Konva.Layer();
		for (let rank = 1; rank <= 8; rank++) {
			for (let file of 'abcdefgh') {
				let square = file + rank;
				let squareContent = this._model.contentAtSquare(square);
				if (squareContent != null && squareContent.value === '?') {
					let newFog = this._createFog(square)
					this._fog.push(newFog);
					ret.add(newFog);
				}
			}
		}
		return ret;
	}

	_setupPieceLayer() {
		logDebug('Setting up piece layer', 'ViewController');
		let ret = new Konva.Layer();
		for (let rank = 1; rank <= 8; rank++) {
			for (let file of 'abcdefgh') {
				let square = file + rank;
				let squareContent = this._model.contentAtSquare(square);
				if (squareContent != null && squareContent.type === 'piece') {
					let newPiece = this._createPiece(
						squareContent.value, squareContent.color,
						this._dimensions.squareSize, square,
						this._model.playersTurn()
					)
					this._boardBuffer.set(square, newPiece);
					ret.add(newPiece.konvaContent);
				}
			}
		}
		return ret;
	}

	_setupInfoOverlayLayer() {
		logDebug('Setting up info overlay layer', 'ViewController');
		let ret = new Konva.Layer();
		let fileLetters = this._boardFlipped ? 'hgfedcba' : 'abcdefgh';
		let alternationTest = this._boardFlipped ? 0 : 1;
		for (let rank = 0; rank < 8; rank++) {
			ret.add(
				new Konva.Text({
					x: this._dimensions.squareSize / 32,
					y: (this._dimensions.squareSize * rank) + this._dimensions.squareSize / 32,
					text: this._boardFlipped ? rank + 1 : 8 - rank,
					fontsize: 5, fill: rank % 2 == alternationTest ? 'black': 'white'
				})
			);
		}
		for (let file = 0; file < 8; file++) {
			ret.add(
				new Konva.Text({
					x: (this._dimensions.squareSize * file) + (this._dimensions.squareSize - (this._dimensions.squareSize / 7)),
					y: (this._dimensions.squareSize * 8) - this._dimensions.squareSize / 5,
					text: fileLetters[file],
					fontsize: 5, fill: file % 2 == alternationTest ? 'white': 'black'
				})
			);
		}
		return ret;
	}

	// It's a bit arbitrary that this method doesn't return the layer like its
	// siblings, but the promotion layer is always temporary.
	_setupPromotionChoiceLayer() {
		this._promotionLayer = new Konva.Layer();
		// Squares and pieces
		let squareGroup = new Konva.Group();
		let squareWidth = this._dimensions.boardWidth / 2;

		let queenSquare = new Konva.Rect({
			x: 0, y: 0, height: squareWidth, width: squareWidth,
			fill: this._config.darkSquareColor
		});
		squareGroup.add(queenSquare);

		let rookSquare = new Konva.Rect({
			x: squareWidth, y: 0, height: squareWidth, width: squareWidth,
			fill: this._config.lightSquareColor
		});
		squareGroup.add(rookSquare);

		let bishopSquare = new Konva.Rect({
			x: 0, y: squareWidth, height: squareWidth, width: squareWidth,
			fill: this._config.lightSquareColor
		});
		squareGroup.add(bishopSquare);

		let knightSquare = new Konva.Rect({
			x: squareWidth, y: squareWidth, height: squareWidth, width: squareWidth,
			fill: this._config.darkSquareColor
		});
		squareGroup.add(knightSquare);

		this._promotionLayer.add(squareGroup);

		let pieceGroup = new Konva.Group();
		let squareCenter = squareWidth / 2;

		let queen = new Konva.Shape({
			x: 0, y: 0,
			width: squareWidth, height: squareWidth,
			sceneFunc: function(context, shape) {
				context.beginPath();
				context.moveTo(squareCenter - (squareWidth / 3), squareCenter - (squareWidth / 8));
				context.lineTo(squareCenter - (squareWidth / 6), squareCenter);
				context.lineTo(squareCenter, squareCenter - (squareWidth / 3));
				context.lineTo(squareCenter + (squareWidth / 6), squareCenter);
				context.lineTo(squareCenter + (squareWidth / 3), squareCenter - (squareWidth / 8));
				context.lineTo(squareCenter + (squareWidth / 4), squareCenter + (squareWidth / 3));
				context.lineTo(squareCenter - (squareWidth / 4), squareCenter + (squareWidth / 3));
				context.closePath();
				context.fillStrokeShape(shape);
			},
			hitFunc: function(context, shape) {
				context.beginPath();
				context.rect(0, 0, squareWidth, squareWidth);
				context.fillStrokeShape(shape);
			}
		});
		queen.on('click', event => {
			this._listener.handlePromotionRequest('q');
		});

		let halfRectWidth = squareWidth / 6;
		let halfHeight = halfRectWidth * 2
		let rook = new Konva.Shape({
			x: squareWidth, y: 0,
			width: squareWidth, height: squareWidth,
			sceneFunc: function(context, shape) {
				context.beginPath();
				context.rect(
					squareCenter - halfRectWidth,
					squareCenter - halfHeight,
					halfRectWidth * 2, halfHeight * 2
				);
				context.fillStrokeShape(shape)
			},
			hitFunc: function(context, shape) {
				context.beginPath();
				context.rect(0, 0, squareWidth, squareWidth);
				context.fillStrokeShape(shape);
			}
		});
		rook.on('click', event => {
			this._listener.handlePromotionRequest('r');
		});

		let bishop = new Konva.Shape({
			x: 0, y: squareWidth,
			width: squareWidth, height: squareWidth,
			sceneFunc: function(context, shape) {
				context.beginPath();
				context.moveTo(squareCenter, squareCenter - (squareWidth / 3));
				context.lineTo(
					squareCenter + (squareWidth / 4),
					squareCenter + (squareWidth / 3)
				);
				context.lineTo(
					squareCenter - (squareWidth / 4),
					squareCenter + (squareWidth / 3)
				);
				context.closePath();
				context.fillStrokeShape(shape);
			},
			hitFunc: function(context, shape) {
				context.beginPath();
				context.rect(0, 0, squareWidth, squareWidth);
				context.fillStrokeShape(shape);
			}
		});
		bishop.on('click', event => {
			this._listener.handlePromotionRequest('b');
		});

		let knight = new Konva.Shape({
			x: squareWidth, y: squareWidth,
			width: squareWidth, height: squareWidth,
			sceneFunc: function(context, shape) {
				context.beginPath();
				context.moveTo(squareCenter - (squareWidth / 4), squareCenter - (squareWidth / 3));
				context.lineTo(squareCenter, squareCenter - (squareWidth / 6));
				context.lineTo(squareCenter + (squareWidth / 4), squareCenter - (squareWidth / 3));
				context.lineTo(squareCenter + (squareWidth / 4), squareCenter);
				context.lineTo(squareCenter + (squareWidth / 8), squareCenter + (squareWidth / 3));
				context.lineTo(squareCenter - (squareWidth / 8), squareCenter + (squareWidth / 3));
				context.lineTo(squareCenter - (squareWidth / 4), squareCenter);
				context.closePath();
				context.fillStrokeShape(shape);
			},
			hitFunc: function(context, shape) {
				context.beginPath();
				context.rect(0, 0, squareWidth, squareWidth);
				context.fillStrokeShape(shape);
			}
		});
		knight.on('click', event => {
			this._listener.handlePromotionRequest('n');
		});

		if (this._model.playerSide === 'b') {
			queen.fill(this._config.pieceColor);
			rook.fill(this._config.pieceColor);
			bishop.fill(this._config.pieceColor);
			knight.fill(this._config.pieceColor);
		} else {
			queen.stroke(this._config.pieceColor);
			queen.strokeWidth(8);
			rook.stroke(this._config.pieceColor);
			rook.strokeWidth(8);
			bishop.stroke(this._config.pieceColor);
			bishop.strokeWidth(8);
			knight.stroke(this._config.pieceColor);
			knight.strokeWidth(8);
		}
		pieceGroup.add(queen);
		pieceGroup.add(rook);
		pieceGroup.add(bishop);
		pieceGroup.add(knight);

		this._promotionLayer.add(pieceGroup);
		this._stage.add(this._promotionLayer);
	}

	_tearDownPromotionChoiceLayer() {
		this._promotionLayer.remove();
		this._promotionLayer.destroy();
	}

	/*** Input Handlers ***/

	_setupClickHandlers() {
		logDebug('Setting up bvc click handlers', 'ViewController');
		// this._canvas.addEventListener('click',
		// 	this._handleSquareClick.bind(this)
		// );
		let flipBoardButton = document.getElementById('flip-board-button');
		flipBoardButton.addEventListener('click',
			this._handleFlipBoardClick.bind(this)
		);
	}

	_tearDownClickHandlers() {
		logDebug('Removing bvc click handlers', 'ViewController')
		// this._canvas.removeEventListener('click', this._handleSquareClick);
		let flipBoardButton = document.getElementById('flip-board-button');
		flipBoardButton.removeEventListener('click', this._handleFlipBoardClick);
	}

	_handleFlipBoardClick() {
		if (this._active) {
			this._flipBoard();
			this._render();
		}
	}

	_handlePieceGrab(event, piece) {
		if (this._active) {
			if (this._model.playersTurn()) {
				if (this._model.movesFrom(piece.square).length > 0) {
					this._highlightSquare(piece.square);
					this._renderMoveOptions(this._model.movesFrom(piece.square));
					// this._selectedPiece = piece;
					let newPos = this._stage.getPointerPosition()
					newPos.x -= this._dimensions.squareSize / 2;
					newPos.y -= this._dimensions.squareSize / 2;
					piece.konvaContent.absolutePosition(newPos);
					this._stage.draw();
					piece.konvaContent.startDrag();
				}
			} else {
				// TODO: Handle pre-moves
			}
		}
	}

	// Note this assumes the piece is the player's
	_handlePieceDrop(event, piece) {
		if (this._active) {
			let pt = {
				x: event.evt.offsetX,
				y: event.evt.offsetY
			}
			// TODO: Handle promotions
			// TODO, just have one function that takes points or squares and
			// returns an object with both details?
			let toSquare = this._pointToSquare(pt);
			let fromSquare = piece.square;
			if (this._model.movesFrom(piece.square).includes(toSquare)) {
				this._highlightSquare(toSquare);
				this._movePieceToSquare(piece, toSquare);
				// TODO: Cleanup the fact that two different formats are
				// required...
				let move = fromSquare + toSquare;
				let structuredMove = {
					from: fromSquare,
					to: toSquare
				};
				if (this._model.potentialPromotion(structuredMove)) {
					// Note that this may no longer be necessary?
					this._listener.handlePromotionEngagement(move);
					this._promoting = true;
					this._setupPromotionChoiceLayer();
				} else if (this._model.pawnCaptureKingPromotion(structuredMove)) {
					this._listener.handleMoveRequest(move + 'q');
				} else {
					this._listener.handleMoveRequest(move);							
				}
			} else {
				// reset to where it was
				this._clearPlayerSquareHighlights();
				this._clearMoveOptions();
				this._movePieceToSquare(piece, piece.square);
			}
			this._render()
			// if (this._model.playersTurn()) {
			// 	if (this._moveOptions(piece.square).includes(toSquare)) {
			// 		this._movePieceToSquare(piece, toSquare);
			// 		this._render();
			// 	}
			// } else {
			// 	// TODO: Handle pre-moves
			// }
		}
	}

	/*** ModelListener Methods ***/

	handleModelReload() {
		// this._selectedPiece = null;
		this._updateBoardState();
		this._render();
	}

	/*** Conversions and Misc Helpers ***/

	_createFog(square) {
		let origin = this._squareToOrigin(square);
		return new Konva.Rect({
			x: origin.x, y: origin.y,
			width: this._dimensions.squareSize,
			height: this._dimensions.squareSize,
			fill: this._config.fogColor,
			opacity: this._config.fogOpacity
		});
	}

	_createPiece(type, side, squareWidth, square, playersTurn = false) {
		logDebug('Creating Piece', 'ViewController');
		let ret = {
			type: type,
			side: side,
			square: square
		}
		let origin = this._squareToOrigin(square);
		let center = {
			x: origin.x + squareWidth / 2,
			y: origin.y + squareWidth / 2
		}
		let squareCenter = squareWidth / 2;
		let konvaContent = new Konva.Shape({
			x: origin.x, y: origin.y,
			width: squareWidth, height: squareWidth,
		});
		// All pieces are custom shapes, even if they would otherwise not need
		switch(type) {
			case 'p':
				konvaContent.sceneFunc(function(context, shape) {
					context.beginPath();
					context.arc(
						squareCenter, squareCenter,
						Math.floor(squareWidth / 4), 0, 2 * Math.PI
					);
					context.fillStrokeShape(shape)
				});
				break;
			case 'r':
				let halfRectWidth = squareWidth / 6;
				let halfHeight = halfRectWidth * 2
				konvaContent.sceneFunc(function(context, shape) {
					context.beginPath();
					context.rect(
						squareCenter - halfRectWidth,
						squareCenter - halfHeight,
						halfRectWidth * 2, halfHeight * 2
					);
					context.fillStrokeShape(shape)
				});
				break;
			case 'n':
				konvaContent.sceneFunc(function(context, shape) {
					context.beginPath();
					context.moveTo(squareCenter - (squareWidth / 4), squareCenter - (squareWidth / 3));
					context.lineTo(squareCenter, squareCenter - (squareWidth / 6));
					context.lineTo(squareCenter + (squareWidth / 4), squareCenter - (squareWidth / 3));
					context.lineTo(squareCenter + (squareWidth / 4), squareCenter);
					context.lineTo(squareCenter + (squareWidth / 8), squareCenter + (squareWidth / 3));
					context.lineTo(squareCenter - (squareWidth / 8), squareCenter + (squareWidth / 3));
					context.lineTo(squareCenter - (squareWidth / 4), squareCenter);
					context.closePath();
					context.fillStrokeShape(shape);
				});
				break;
			case 'b':
				konvaContent.sceneFunc(function(context, shape) {
					context.beginPath();
					context.moveTo(squareCenter, squareCenter - (squareWidth / 3));
					context.lineTo(
						squareCenter + (squareWidth / 4),
						squareCenter + (squareWidth / 3)
					);
					context.lineTo(
						squareCenter - (squareWidth / 4),
						squareCenter + (squareWidth / 3)
					);
					context.closePath();
					context.fillStrokeShape(shape);
				});
				break;
			case 'q':
				konvaContent.sceneFunc(function(context, shape) {
					context.beginPath();
					context.moveTo(squareCenter - (squareWidth / 3), squareCenter - (squareWidth / 8));
					context.lineTo(squareCenter - (squareWidth / 6), squareCenter);
					context.lineTo(squareCenter, squareCenter - (squareWidth / 3));
					context.lineTo(squareCenter + (squareWidth / 6), squareCenter);
					context.lineTo(squareCenter + (squareWidth / 3), squareCenter - (squareWidth / 8));
					context.lineTo(squareCenter + (squareWidth / 4), squareCenter + (squareWidth / 3));
					context.lineTo(squareCenter - (squareWidth / 4), squareCenter + (squareWidth / 3));
					context.closePath();
					context.fillStrokeShape(shape);
				});
				break;
			case 'k':
				konvaContent.sceneFunc(function(context, shape) {
					context.beginPath();
					context.arc(
						squareCenter, squareCenter - (squareWidth / 4),
						Math.floor(squareWidth / 8), 0, 2 * Math.PI
					);
					context.moveTo(squareCenter - (squareWidth / 3), squareCenter - (squareWidth / 3))
					context.lineTo(squareCenter, squareCenter);
					context.lineTo(squareCenter + (squareWidth / 3), squareCenter - (squareWidth / 3));
					context.lineTo(squareCenter + (squareWidth / 3), squareCenter + (squareWidth / 3));
					context.lineTo(squareCenter - (squareWidth / 3), squareCenter + (squareWidth / 3));
					context.closePath();
					context.fillStrokeShape(shape);
				});
				break;
		}
		let fillColor = (playersTurn && type === 'k') ?
			this._config.playersTurnColor :
			this._config.pieceColor;
		if (side === 'b') {
			konvaContent.fill(fillColor);
		} else {
			konvaContent.stroke(fillColor);
			konvaContent.strokeWidth(2);
		}
		// players piece
		if (side === this._model.playerSide) {
			let self = this;
			konvaContent.hitFunc(function(context, shape) {
				context.beginPath();
				context.rect(0, 0, squareWidth, squareWidth);
				context.fillStrokeShape(shape);
			});
			// Snap to pointer, note we have to manually begin the drag
			// in this function as opposed to simply setting ret.draggable
			// to true since that messes  with the snapping.
			konvaContent.on('mousedown', function(event) {
				self._handlePieceGrab(event, ret)
			})
			konvaContent.on('dragend', function(event) {
				self._handlePieceDrop(event, ret);
			});
		}
		ret.konvaContent = konvaContent;
		return ret
	}

	// this assumes ranks and files proceed from left to right, and top to
	// bottom
	_squareToOrigin(square) {
		let ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];
		let files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
		if (this._boardFlipped) {
			ranks.reverse();
			files.reverse();
		}
		let x = files.indexOf(square[0]) * this._dimensions.squareSize;
		let y = ranks.indexOf(square[1]) * this._dimensions.squareSize;
		return {x, y};
	}

	_pointToSquare(point) {
		let ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];
		let files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
		if (this._boardFlipped) {
			ranks.reverse();
			files.reverse();
		}
		let rank = ranks[Math.floor(point.y / this._dimensions.squareSize)];
		let file = files[Math.floor(point.x / this._dimensions.squareSize)];
		return file + rank;
	}

	/*** View Update Methods ***/

	_flipBoard() {
		logDebug('Flipping board', 'ViewController')
		let playerWhite = document.getElementById('player-white'); 
		let playerBlack = document.getElementById('player-black');
		swapEl(playerWhite, playerBlack);
		this._boardFlipped = !this._boardFlipped;
		// this._render();
	}

	_clearMoveOptions() {
		for (let option of this._moveOptions) {
			option.destroy();
		}
		this._moveOptions = [];
	}

	_clearSquareHighlights() {
		for (let highlight of this._highlightedSquares) {
			highlight.destroy();
		}
		this._highlightedSquares = [];
		if (this._opponentSquareHighlight !== null) {
			this._opponentSquareHighlight.destroy();
			this._opponentSquareHighlight = null;
		}
	}

	_clearPlayerSquareHighlights() {
		for (let highlight of this._highlightedSquares) {
			highlight.destroy();
		}
		this._highlightedSquares = [];
	}

	_highlightSquare(square, opponent = false) {
		let origin = this._squareToOrigin(square);
		let newHighlight = new Konva.Rect({
			x: origin.x, y: origin.y,
			width: this._dimensions.squareSize,
			height: this._dimensions.squareSize,
			fill: this._config.infoObjectColor,
			opacity: this._config.infoObjectOpacity
		});
		if (opponent) {
			this._opponentSquareHighlight = newHighlight;
		} else {
			this._highlightedSquares.push(newHighlight);
		}
		this._infoOverlayLayer.add(newHighlight);
	}

	_renderMoveOptions(moves) {
		let cirlceRadius = this._dimensions.squareSize / 8;
		for (let square of moves) {
			let origin = this._squareToOrigin(square);
			let center = {
				x: origin.x + this._dimensions.squareSize / 2,
				y: origin.y + this._dimensions.squareSize / 2
			}
			let newMoveOption = new Konva.Circle({
				x: center.x, y: center.y,
				radius: cirlceRadius,
				fill: this._config.infoObjectColor,
				opacity: this._config.infoObjectOpacity
			});
			this._infoOverlayLayer.add(newMoveOption);
			this._moveOptions.push(newMoveOption);
		}
	}

	_clearFog() {
		for (let fog of this._fog) {
			fog.destroy();
		}
		this._fog = [];
	}

	_clearPieces() {
		for (let piece of this._boardBuffer.values()) {
			piece.konvaContent.destroy();
		}
		this._boardBuffer.clear();
	}

	// When updating the boardstate, care should be taken to differentiate
	// between a dark view and a historical/analysis or spectator view. When in
	// a dark view for instance, it's obvious that you should draw fog of war on
	// positions the player can't see, but you also need to remember not to
	// animate opponent moves, even if the piece is moving into a square the
	// player has vision on, because the animation may give away the sqaure the
	// piece was moved from.
	//
	// For now, animation has been put on hold until I come up with a pleasant
	// way of animating between arbitrary fens.
	_updateBoardState(animate = false) {
		logDebug('Updating board state', 'ViewController');
		if (this._promoting) {
			this._promoting = false;
			this._tearDownPromotionChoiceLayer();
		}
		this._clearFog();
		this._clearMoveOptions();
		this._clearPieces();
		// TODO: diff the current and new fen and only make necessary changes
		for (let rank = 1; rank <= 8; rank++) {
			for (let file of 'abcdefgh') {
				let square = file + rank;
				let squareContent = this._model.contentAtSquare(square);
				if (squareContent != null &&
					squareContent.type === 'piece' || squareContent.value === '?') {
					if (squareContent.type === 'piece') {
						let newPiece = this._createPiece(
							squareContent.value, squareContent.color,
							this._dimensions.squareSize, square,
							this._model.playersTurn()
						);
						this._boardBuffer.set(square, newPiece);
						this._pieceLayer.add(newPiece.konvaContent);
					} else {
						let newFog = this._createFog(square);
						this._fog.push(newFog);
						this._fogLayer.add(newFog);
					}
				}
			}
		}
		let move = this._model.latestMove;
		if (move !== null) {
			let from = move.slice(0, 2);
			let to = move.slice(2, 4);
			if (this._model.playersTurn()) {
				this._clearSquareHighlights();
				// TODO/NOTE: This is a bit of a hack right now. This only works
				// because move events currently leak the move even if the
				// player shouldn't be able to see it. When the websocket events
				// are reworked not to do this, it should more simple like
				// checking if the move is null or somthing.
				if (this._boardBuffer.has(to)) {
					this._highlightSquare(to, true);
				}
			} else {
				this._clearSquareHighlights();
				this._highlightSquare(from);
				this._highlightSquare(to);
			}
		}
	}

	_movePieceToSquare(piece, square, animate = false) {
		let pt = this._squareToOrigin(square);
		// For now, we don't actually update the pieces squares, we only move
		// them visually as an indication that the client has recognized a move
		// attempt. The internal movement of the pieces will occur with the
		// model reloads based on the server response.

		// this._boardBuffer.delete(piece.square);
		// piece.square = square;
		// if (this._boardBuffer.has(square)) {
		// 	this._boardBuffer.get(square).konvaContent.destroy();
		// 	this._boardBuffer.delete(square);
		// }
		// this._boardBuffer.set(square, piece);
		if (animate) {
			logDebug('Piece movement (Animated)', 'ViewController');
			let movement = new Konva.Tween({
				node: piece.konvaContent,
				duration: this._config.pieceMovementSpeed,
				x: pt.x,
				y: pt.y
			});
			// This maybe should be kept as a reference and then called in the
			// render function
			movement.play();
		} else {
			logDebug('Piece Movement (Not Animated)', 'ViewController');
			piece.konvaContent.x(pt.x);
			piece.konvaContent.y(pt.y);
		}
	}

	_render() {
		logDebug('Rendering', 'ViewController')
		// Might not be the most efficient place for this, but will definitely
		// work.
		if (this._model.playersTurn()) {
			utilities.changeFavicon('favicon_player_turn.ico');
		} else {
			utilities.changeFavicon('favicon.ico');
		}
		this._stage.draw();
	}

}

// Like the class name implies, this controls the board view. It handles all
// player actions. This implementation relies on the Canvas API. There are a few
// non-canvas elements that are also controlled here.
class CanvasBoardViewController {

	constructor(model, squareWidth = 60) {
		logDebug('Constructing CanvasBoardViewController.', 'ViewController');
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

			this._clickHandlersSetup = false;
			if (this._active) {
				this._clickHandlersSetup = true;
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
		logDebug('Setting up click handlers', 'Setup');
		this._canvas.addEventListener('click',
			this._handleSquareClick.bind(this)
		);
		let flipBoardButton = document.getElementById('flip-board-button');
		flipBoardButton.addEventListener('click',
			this._handleFlipBoardClick.bind(this)
		);
	}

	_tearDownClickHandlers() {
		logDebug('Removing click handlers', 'Teardown')
		this._canvas.removeEventListener('click', this._handleSquareClick);
		let flipBoardButton = document.getElementById('flip-board-button');
		flipBoardButton.addEventListener('click', this._handleFlipBoardClick);
	}

	_handleFlipBoardClick() {
		this._flipBoard();
	}

	get _promoting() {
		return this._model.promoting;
	}

	// TODO: Refactor
	_handleSquareClick(event) {
		logDebug('Handling square click', 'Input');
		if (this._active) {
			let clickPoint = {x: event.offsetX, y: event.offsetY};
			if (this._promoting) {
				let pieces = ['n', 'b', 'r', 'q'];
				let rowOffset = Math.floor(clickPoint.y / (this._height / 2));
				let col = Math.floor(clickPoint.x / (this._width / 2));
				let pieceChosen = pieces[(rowOffset * 2) + col];
				logDebug(`Promotion choice ${pieceChosen}`, 'Click');
				this._listener.handlePromotionRequest(pieceChosen);
			} else {
				let square = this._pointToSquare(clickPoint);
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
						// TODO: remove this once all moves are standardized.
						let newFormatMove = {
							from: this._selectedSquare,
							to: square
						}
						if (this._model.potentialPromotion(newFormatMove)) {
							this._listener.handlePromotionEngagement(move);
							this._render();
						// This is a workaround for the fact that the chess
						// library on the backend doesn't consider a pawn
						// capturing the king without promoting to be a
						// pseudo-legal move. An issue was raised on github, but
						// the conclusion was that the behavior wanted here
						// would be better implemented with a variant. All the
						// below does is append a queen promotion to the move.
						} else if (
							this._model.pawnCaptureKingPromotion(newFormatMove)
						) {
							this._listener.handleMoveRequest(move + 'q');
						} else {
							this._listener.handleMoveRequest(move);							
						}
					} else {
						this._clearMoveOptions();
					}
					this._render();
				}
			}
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
		if (!this._clickHandlersSetup) {
			this._clickHandlersSetup = true;
			this._setupClickHandlers();
		}
		this._render();
	}

	handlePromotionMove() {
		this._promoting = true;
	}

	handleGameOver(winner) {
		this._tearDownClickHandlers();
		this._render()
	}

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

	_drawPiece(piece, origin, squareWidth) {
		let center = {
			x: origin.x + Math.floor(squareWidth / 2),
			y: origin.y + Math.floor(squareWidth / 2)
		}
		this._ctx.fillStyle = 'black';
		if (piece.type === 'p') { // pawns
			let rad = Math.floor(squareWidth / 4);
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
				center.x - (squareWidth / 4),
				center.y - (squareWidth / 3)
			);
			// central crevice
			this._ctx.lineTo(
				center.x, center.y - (squareWidth / 6)
			)
			// right ear
			this._ctx.lineTo(
				center.x + (squareWidth / 4),
				center.y - (squareWidth / 3)
			);
			// right eye
			this._ctx.lineTo(
				center.x + (squareWidth / 4),
				center.y,
			);
			// right mouth
			this._ctx.lineTo(
				center.x + (squareWidth / 8),
				center.y + (squareWidth / 3)
			);
			// left mouth
			this._ctx.lineTo(
				center.x - (squareWidth / 8),
				center.y + (squareWidth / 3)
			);
			// left eye
			this._ctx.lineTo(
				center.x - (squareWidth / 4),
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
			let length = squareWidth / 3;
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
				center.y - (squareWidth / 3)
			);
			this._ctx.lineTo(
				center.x + (squareWidth / 4),
				center.y + (squareWidth / 3)
			);
			this._ctx.lineTo(
				center.x - (squareWidth / 4),
				center.y + (squareWidth / 3)
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
				center.x - (squareWidth / 3),
				center.y - (squareWidth / 3),
			);
			// central crevice
			this._ctx.lineTo(center.x, center.y);
			// right spike
			this._ctx.lineTo(
				center.x + (squareWidth / 3),
				center.y - (squareWidth / 3),
			);
			// right base
			this._ctx.lineTo(
				center.x + (squareWidth / 3),
				center.y + (squareWidth / 3)
			);
			// left base
			this._ctx.lineTo(
				center.x - (squareWidth / 3),
				center.y + (squareWidth / 3)
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
				center.y - (squareWidth / 4),
				Math.floor(squareWidth / 8),
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
				center.x - (squareWidth / 3),
				center.y - (squareWidth / 8),
			);
			// left crevice
			this._ctx.lineTo(
				center.x - (squareWidth / 6),
				center.y
			);
			// central spike
			this._ctx.lineTo(
				center.x,
				center.y - (squareWidth / 3),
			);
			// right crevice
			this._ctx.lineTo(
				center.x + (squareWidth / 6),
				center.y
			);
			// right spike
			this._ctx.lineTo(
				center.x + (squareWidth / 3),
				center.y - (squareWidth / 8)
			);
			// right base
			this._ctx.lineTo(
				center.x + (squareWidth / 4),
				center.y + (squareWidth / 3)
			);
			// left base
			this._ctx.lineTo(
				center.x - (squareWidth / 4),
				center.y + (squareWidth / 3)
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
		if (this._promoting) {
			// TODO: Render this on a new canvas layer on top of the original
			// board?
			// render cross lines
			this._helperDrawLine(
				{ x: this._width / 2, y: 0 },
				{ x: this._width / 2, y: this._height }
			);
			this._helperDrawLine(
				{ x: 0, y: this._height / 2 },
				{ x: this._width, y: this._height / 2 }
			);
			// Fill squares
			this._ctx.fillStyle = '#6aa1c8';
			this._ctx.fillRect(
				(this._width / 2) + 1, 0,
				(this._width / 2) - 1, (this._height / 2) - 1
			);
			this._ctx.fillRect(
				0, (this._height / 2) + 1,
				(this._width / 2) - 1, (this._height / 2) - 1
			);
			this._ctx.fillStyle = 'black';
			// render piece options
			let pieceColor = this._model.playerSide;
			this._drawPiece(
				{ type: 'n', color: pieceColor },
				{ x: 0, y: 0 },
				this._width / 2 - 1
			);
			this._drawPiece(
				{ type: 'b', color: pieceColor },
				{ x: this._width / 2, y: 0 },
				this._width / 2 - 1
			);
			this._drawPiece(
				{ type: 'r', color: pieceColor },
				{ x: 0, y: this._height / 2 },
				this._width / 2 - 1
			);
			this._drawPiece(
				{ type: 'q', color: pieceColor },
				{ x: this._width / 2, y: this._height / 2 },
				this._width / 2 - 1
			);
		} else {
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
							this._drawPiece(piece, origin, this._squareWidth);
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
			if (this._model.playersTurn()) {
				utilities.changeFavicon('favicon_player_turn.ico');
			} else {
				utilities.changeFavicon('favicon.ico');
			}
		}
	}

}

// Main class
class Match {
	
	constructor(config, matchData, playerData) {
		this._mm = new MatchModel(matchData, playerData);
		// this._bvc = new CanvasBoardViewController(this._mm);
		// testing
		this._bvc = new KonvaBoardViewController(this._mm);

		this._bvc.setListener(this);
		this._api = new APIHandler(config);
		this._wsh = new WebsocketHandler(config, matchData.connection_token);
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

	handlePromotionEngagement(move) {
		this._mm.bufferPromotion(move);
	}

	// Note this doesn't do any checks for corrupted state...
	handlePromotionRequest(piece) {
		let move = this._mm.promotionMove + piece;
		this._api.requestMove(this._mm, move)
	}

	/* Websocket Event Listener methods */
	handleMatchBegin() {
		this.syncModelWithRemote();
	}

	handleMoveEvent(event) {
		if (this._mm.promoting) {
			this._mm.clearPromotion();
		}
		this._mm.latestMove = event.uci_string;
		this.syncModelWithRemote();
	}

	handleMatchFinish(winningPlayerJSON) {
		this.syncModelWithRemote();
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