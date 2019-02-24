from flask import Blueprint

users = Blueprint('users', __name__)

from dark_chess_api.modules.users import endpoints