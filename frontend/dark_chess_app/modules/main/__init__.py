from flask import Blueprint

main = Blueprint('main', __name__)

from dark_chess_app.modules.main import routes