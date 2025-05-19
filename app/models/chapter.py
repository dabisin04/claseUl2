from config.db import db, ma
from datetime import datetime
import uuid
import json

class Chapter(db.Model):
    __tablename__ = 'chapters'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = db.Column(db.String(36), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)  # JSON codificado como texto
    upload_date = db.Column(db.String(50), default=lambda: datetime.now().isoformat())
    publication_date = db.Column(db.DateTime, nullable=True)
    chapter_number = db.Column(db.Integer, nullable=False)
    views = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    ratings_count = db.Column(db.Integer, default=0)
    reports = db.Column(db.Integer, default=0)

    def __init__(
        self, book_id, title, content, upload_date, publication_date,
        chapter_number, views=0, rating=0.0, ratings_count=0, reports=0, id=None
    ):
        self.id = id or str(uuid.uuid4())
        self.book_id = book_id
        self.title = title
        self.content = json.dumps(content) if isinstance(content, dict) else content
        self.upload_date = upload_date or datetime.now().isoformat()
        self.publication_date = publication_date
        self.chapter_number = chapter_number
        self.views = views
        self.rating = rating
        self.ratings_count = ratings_count
        self.reports = reports

    def to_dict(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "title": self.title,
            "content": json.loads(self.content) if self.content else None,
            "upload_date": self.upload_date,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "chapter_number": self.chapter_number,
            "views": self.views,
            "rating": self.rating,
            "ratings_count": self.ratings_count,
            "reports": self.reports
        }

class ChapterSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'book_id', 'title', 'content', 'upload_date', 'publication_date',
            'chapter_number', 'views', 'rating', 'ratings_count', 'reports'
        )
