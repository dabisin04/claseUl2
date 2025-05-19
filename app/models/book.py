from config.db import db, ma
from datetime import datetime
import uuid
import json

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    author_id = db.Column(db.String(36), nullable=False)
    description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(100), nullable=False)
    additional_genres = db.Column(db.Text, default='[]')  # Almacena JSON como string
    upload_date = db.Column(db.String(50), nullable=False, default=lambda: datetime.now().isoformat())
    publication_date = db.Column(db.DateTime, nullable=True)
    views = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    ratings_count = db.Column(db.Integer, default=0)
    reports = db.Column(db.Integer, default=0)
    content = db.Column(db.Text, nullable=True)  # JSON serializado
    is_trashed = db.Column(db.Boolean, default=False)
    has_chapters = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')
    content_type = db.Column(db.String(20), default='book')

    def __init__(
        self, title, author_id, genre, upload_date, description=None,
        additional_genres=None, publication_date=None, views=0, rating=0.0,
        ratings_count=0, reports=0, content=None, is_trashed=False,
        has_chapters=False, status='pending', content_type='book', id=None
    ):
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.author_id = author_id
        self.description = description
        self.genre = genre
        self.additional_genres = json.dumps(additional_genres or [])
        self.upload_date = upload_date or datetime.now().isoformat()
        self.publication_date = publication_date
        self.views = views
        self.rating = rating
        self.ratings_count = ratings_count
        self.reports = reports
        self.content = json.dumps(content) if isinstance(content, dict) else content
        self.is_trashed = is_trashed
        self.has_chapters = has_chapters
        self.status = status
        self.content_type = content_type

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author_id': self.author_id,
            'description': self.description,
            'genre': self.genre,
            'additional_genres': json.loads(self.additional_genres or '[]'),
            'upload_date': self.upload_date,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'views': self.views,
            'rating': self.rating,
            'ratings_count': self.ratings_count,
            'reports': self.reports,
            'content': json.loads(self.content or '{}') if self.content else None,
            'is_trashed': self.is_trashed,
            'has_chapters': self.has_chapters,
            'status': self.status,
            'content_type': self.content_type
        }

    @staticmethod
    def from_dict(data):
        return Book(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', 'Sin título'),
            author_id=data.get('author_id', 'Desconocido'),
            description=data.get('description'),
            genre=data.get('genre', 'Sin género'),
            additional_genres=data.get('additional_genres', []),
            upload_date=data.get('upload_date', datetime.now().isoformat()),
            publication_date=datetime.fromisoformat(data['publication_date']) if data.get('publication_date') else None,
            views=data.get('views', 0),
            rating=float(data.get('rating', 0.0)),
            ratings_count=data.get('ratings_count', 0),
            reports=data.get('reports', 0),
            content=data.get('content'),
            is_trashed=bool(data.get('is_trashed', False)),
            has_chapters=bool(data.get('has_chapters', False)),
            status=data.get('status', 'pending'),
            content_type=data.get('content_type', 'book')
        )

class BookSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'title', 'author_id', 'description', 'genre', 'additional_genres',
            'upload_date', 'publication_date', 'views', 'rating', 'ratings_count',
            'reports', 'content', 'is_trashed', 'has_chapters', 'status', 'content_type'
        )
