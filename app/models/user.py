from config.db import db, ma
import uuid

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    salt = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, email, password, salt=None, bio=None, is_admin=False, id=None):
        self.id = id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password = password
        self.salt = salt
        self.bio = bio
        self.is_admin = is_admin

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'salt': self.salt,
            'bio': self.bio,
            'is_admin': self.is_admin,
        }

    @staticmethod
    def from_dict(data):
        return User(
            id=data.get('id'),
            username=data['username'],
            email=data['email'],
            password=data['password'],
            salt=data.get('salt'),
            bio=data.get('bio'),
            is_admin=data.get('is_admin', False)
        )

class UserSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'username', 'email', 'password', 'salt', 'bio', 'is_admin'
        )
