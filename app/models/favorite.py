from config.db import db, ma
import uuid

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    book_id = db.Column(db.String(36), nullable=False)

    def __init__(self, user_id, book_id, id=None):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.book_id = book_id

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
        }

class FavoriteSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'book_id')
