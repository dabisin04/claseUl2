from config.db import db, app, ma

class Taks(db.Model):
    __tablename__ ='tbltaks'
    id = db.Column(db.Integer, primary_key = True)
    nametak = db.Column(db.String(50))
    idUser_fk = db.Column(db.Integer, db.ForeignKey('tblusers.id'))
    idCategory_fk = db.Column(db.Integer,db.ForeignKey('tblcategory.id'))
    def __init__(self, nametak, idUser_fk):
        self.nametak = nametak
        self.idUser_fk = idUser_fk

with app.app_context():
    db.create_all()

class TaksSchema(ma.Schema):
    class Meta:
        fields =('id', 'nametak', 'idUser_fk', 'idCategory_fk')