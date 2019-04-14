// This class (for now) simply handles the recieving of move events
// from the server.
class WebsocketHandler {

}

// This is just a client cache for the backend's model. Its main
// intention is to allow client-side move verification.
class MatchModel {

	constructor(matchData) {
		this._board = new Chess();
		this._board.load(matchData.history[matchData.history.length - 1]);
		this._matchId = matchData.id;
	}

	syncWithRemote() {
		fetch(`${config.apiRoot}/match/${this._matchId}`, {
			method: 'GET',
			headers: {
				'Authorization': `Bearer ${config.token}`
			}
		}).then(response => {
			return response.json();
		}).then(json => {
			this._board.load(json.current_fen),
		});
	}

	reload(fen) {
		return this._board.load(fen);
	}

	// expects same notation as used by backend, namely uci
	validMove(move) {
		return this._board.move(move, {sloppy: true}) != null;
	}

	pieceAt(square) {
		return this._board.get(square);
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

	_handleSquareClick(event) {
		let square = event.target.id;
		let pieceJSON = JSON.stringify(this._model.pieceAt(square));
		console.log('Piece at ' + square + ': ' + pieceJSON);
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

mm = new MatchModel(matchData);
bvc = new BoardViewController(mm);