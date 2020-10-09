from flask import Blueprint

errors = Blueprint('errors', __name__)

from dark_chess_app.modules.errors import handlers