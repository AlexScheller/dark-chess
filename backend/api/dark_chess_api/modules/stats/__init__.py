from flask import Blueprint

stats = Blueprint('stats', __name__)

from dark_chess_api.modules.stats import models, endpoints