from flask import Blueprint

match = Blueprint('match', __name__)

from dark_chess_app.modules.match import routes, endpoints