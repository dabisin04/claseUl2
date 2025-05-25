from config.db import db, ma
import uuid

class ReportAlert(db.Model):
    __tablename__ = 'report_alerts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = db.Column(db.String(36), db.ForeignKey('books.id'), nullable=False)
    report_reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='alert')  # 'alert', 'removed', 'restored'
    created_at = db.Column(db.String(50), nullable=False)  # Longitud suficiente para timestamp ISO

    def __init__(self, book_id, report_reason, status='alert', created_at=None, id=None):
        from datetime import datetime
        self.id = id or str(uuid.uuid4())
        self.book_id = book_id
        self.report_reason = report_reason
        self.status = status
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'report_reason': self.report_reason,
            'status': self.status,
            'created_at': self.created_at,
        }

    @staticmethod
    def from_dict(data):
        return ReportAlert(
            id=data.get('id'),
            book_id=data['book_id'],
            report_reason=data['report_reason'],
            status=data.get('status', 'alert'),
            created_at=data.get('created_at'),
        )

class ReportAlertSchema(ma.Schema):
    class Meta:
        fields = ('id', 'book_id', 'report_reason', 'status', 'created_at')
