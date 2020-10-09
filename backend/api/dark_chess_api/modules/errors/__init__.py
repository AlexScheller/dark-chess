from flask import Blueprint

errors = Blueprint('errors', __name__)

from dark_chess_api.modules.errors import handlers