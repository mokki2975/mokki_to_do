from .extensions import db
from werkzeug.security import generate_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'
    
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task = db.Column(db.String(120), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Task {self.task} (Done: {self.done})>'