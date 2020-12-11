from dark_chess_api import endpointer

from dark_chess_api.modules.stats import stats
from dark_chess_api.modules.stats.models import UserStatBlock
from dark_chess_api.modules.users.auth import token_auth

@endpointer.route('/statblock/<int:id>', methods=['GET'], bp=stats,
	responds={
		200: { 'StatBlock': UserStatBlock.mock_dict() },
		404: None
	},
	auth='token (bearer)'
)
@token_auth.login_required
def get_user_stat_block(id):
	stat_block = UserStatBlock.query.get_or_404(id)
	ret = stat_block.as_dict()
	ret['user_id'] = id
	return ret