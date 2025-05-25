from config.db import db, ma
import uuid
from models.user import User

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    target_id = db.Column(db.String(36), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)  # 'user', 'book', 'comment'
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'reviewed', 'dismissed'
    admin_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    # Relaciones
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reports_made')
    admin = db.relationship('User', foreign_keys=[admin_id], backref='reports_handled')

    def __init__(self, reporter_id, target_id, target_type, reason, status='pending', admin_id=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.reporter_id = reporter_id
        self.target_id = target_id
        self.target_type = target_type
        self.reason = reason
        self.status = status
        self.admin_id = admin_id

    def to_dict(self):
        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'target_id': self.target_id,
            'target_type': self.target_type,
            'reason': self.reason,
            'status': self.status,
            'admin_id': self.admin_id,
        }

    @staticmethod
    def from_dict(data):
        return Report(
            id=data.get('id'),
            reporter_id=data['reporter_id'],
            target_id=data['target_id'],
            target_type=data['target_type'],
            reason=data['reason'],
            status=data.get('status', 'pending'),
            admin_id=data.get('admin_id'),
        )

class ReportSchema(ma.Schema):
    class Meta:
        fields = ('id', 'reporter_id', 'target_id', 'target_type', 'reason', 'status', 'admin_id')
