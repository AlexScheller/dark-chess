# class UserStatBlock(db.Model):

# 	### intrinsic ###
# 	games_played = db.Column(db.Integer)
# 	games_won = db.Column(db.Integer)
# 	games_lost = db.Column(db.Integer)
# 	rating = db.Column(db.Integer)

# 	### relationship ###
# 	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
# 	user = db.relationship('User', back_populates='stat_block')