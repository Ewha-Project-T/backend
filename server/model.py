from server import db

class User(db.Model):
    __tablename__ = "user"

    user_no = db.Column(db.Integer,primary_key=True)
    id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), unique=True, nullable=False)
    permission = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    login_fail_limit = db.Column(db.Integer, default=0)

