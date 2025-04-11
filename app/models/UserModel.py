from config.db import db, app, ma

class Users(db.Model):
    __tablename__ ='tblusers'

    id = db.Column(db.Integer, primary_key = True) 
    fullname = db.Column(db.String(50))
    email = db.Column(db.String(50))

    def __init__(self, fullname, email):
        self.fullname = fullname
        self.email = email
    
with app.app_context():
    db.create_all()
    
class UsersSchema(ma.Schema):
    class Meta:
        fields = ('id','fullname','email')