from flask import Blueprint

matches = Blueprint('matches', __name__)

from dark_chess_api.modules.matches import endpoints