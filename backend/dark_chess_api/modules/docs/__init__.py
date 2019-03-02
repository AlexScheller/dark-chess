from flask import Blueprint

docs = Blueprint('docs', __name__)

from dark_chess_api.modules.docs import routes