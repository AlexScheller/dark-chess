from dark_chess_api.modules.stats import stats
from dark_chess_api.modules.stats.models import UserStatBlock
from dark_chess_api.modules.auth.utils import token_auth

@stats.route('/statblock/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user_stat_block(id):
	stat_block = UserStatBlock.query.get_or_404(id)
	ret = stat_block.as_dict()
	ret['user_id'] = id
	return ret