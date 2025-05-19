from config.db import db, ma
import uuid
from datetime import datetime

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    book_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().isoformat())
    parent_comment_id = db.Column(db.String(36), nullable=True)
    root_comment_id = db.Column(db.String(36), nullable=True)
    reports = db.Column(db.Integer, default=0)

    def __init__(
        self,
        user_id,
        book_id,
        content,
        timestamp=None,
        parent_comment_id=None,
        root_comment_id=None,
        reports=0,
        id=None
    ):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.book_id = book_id
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.parent_comment_id = parent_comment_id
        self.root_comment_id = root_comment_id or (self.id if parent_comment_id is None else None)
        self.reports = reports

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'content': self.content,
            'timestamp': self.timestamp,
            'parent_comment_id': self.parent_comment_id,
            'root_comment_id': self.root_comment_id,
            'reports': self.reports,
        }

class CommentSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'user_id', 'book_id', 'content', 'timestamp',
            'parent_comment_id', 'root_comment_id', 'reports'
        )
