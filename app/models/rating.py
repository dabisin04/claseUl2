from config.db import db, ma
import uuid
from datetime import datetime

class BookRating(db.Model):
    __tablename__ = 'book_ratings'

    id = db.Column(db.String(80), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    book_id = db.Column(db.String(36), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().isoformat())

    def __init__(self, user_id, book_id, rating, id=None, timestamp=None):
        assert 1 <= rating <= 5, "El rating debe estar entre 1 y 5"
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.book_id = book_id
        self.rating = rating
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'rating': self.rating,
            'timestamp': self.timestamp,
        }

class BookRatingSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'book_id', 'rating', 'timestamp')
