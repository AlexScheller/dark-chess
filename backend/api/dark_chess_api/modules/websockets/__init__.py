from flask import Blueprint

websockets = Blueprint('websockets', __name__)

from dark_chess_api.modules.websockets import events