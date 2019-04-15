// This class (for now) simply handles the recieving of move events
// from the server.
class WebsocketHandler {

}

class APIHandler {

	constructor(config) {
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
			console.log('(API Event) requesting move: ' + move);
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
				console.log('(Server Response)')
				console.log(response)
			}
			model.reload(json.current_fen);
		});
	}

}

// This is just a client cache for the backend's model. Its main
// intention is to allow client-side move verification.
class MatchModel {

	constructor(matchData, playerData) {
		this._board = new Chess();
		this._board.load(matchData.history[matchData.history.length - 1]);
		this._matchId = matchData.id;
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

	syncWithRemote() {
		this._api.syncMatchState(this, this._matchId);
	}

	reload(fen) {
		return this._board.load(fen);
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


// Like the class name implies, this controls the board view
class BoardViewController {

	constructor(model) {
		this._pieces = {
			w: { p: '♙', r: '♖', n: '♘', b: '♗', q: '♕', k: '♔' },
			b: { p: '♟', r: '♜', n: '♞', b: '♝', q: '♛', k: '♚' },
		};
		this._setupClickHandlers();
		this._model = model;
		this._selectedSquare = null;
		this._render();
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
			console.log('(Render Event) rendering move options');
		}
		this._selectedSquare = fromSquare;
		document.getElementById(fromSquare).classList.add('selected-square');
		for (const move of this._model.movesFrom(fromSquare)) {
			if (config.debug) {
				console.log('(Render Event) rendering move option: ' + fromSquare + move.to);
			}
			document.getElementById(move.to).classList.add('move-option');
		}
	}

	_handleSquareClick(event) {
		let square = event.target.id;
		if (config.debug) {
			let pieceJSON = JSON.stringify(this._model.pieceAt(square));
			console.log('(Click Event) Piece at ' + square + ': ' + pieceJSON);
		}
		if (this._model.playersTurn()) {
			if (event.target.classList.contains('move-option')) {
				let move = this._selectedSquare + square;
				this.api.requestMove(this._model, move);
			} else if (this._model.playersPiece(square)) {
				this._renderMoveOptions(square);
			}
		}
	}

	_render() {
		for (let row = 1; row <= 8; row++) {
			for (const col of 'abcdefgh') {
				let piece = this._model.pieceAt(col + row);
				if (piece != null) {
					let pieceText = this._pieces[piece.color][piece.type];
					document.getElementById(col + row).innerText = pieceText;
				}
			}
		}
	}

}

mm = new MatchModel(matchData, playerData);
bvc = new BoardViewController(mm);