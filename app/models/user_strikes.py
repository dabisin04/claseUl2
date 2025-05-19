from config.db import db, ma
import uuid

class UserStrike(db.Model):
    __tablename__ = 'user_strikes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    strike_count = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, user_id, reason, strike_count=1, is_active=True, id=None):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.reason = reason
        self.strike_count = strike_count
        self.is_active = is_active

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reason': self.reason,
            'strike_count': self.strike_count,
            'is_active': self.is_active,
        }

    @staticmethod
    def from_dict(data):
        return UserStrike(
            id=data.get('id'),
            user_id=data['user_id'],
            reason=data['reason'],
            strike_count=data.get('strike_count', 1),
            is_active=data.get('is_active', True),
        )

class UserStrikeSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'reason', 'strike_count', 'is_active')
