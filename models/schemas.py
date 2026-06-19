from .database import db
from datetime import datetime

class Flashcard(db.Model):
    id = db.Column(db.Float, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'grammar' or 'vocab'
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    source = db.Column(db.String(20))  # 'conversation' or 'vocabulary'
    added = db.Column(db.DateTime, default=datetime.utcnow)

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True, nullable=False)
    pos = db.Column(db.String(20))  # part of speech
    definition = db.Column(db.Text, nullable=False)
    examples = db.Column(db.Text)  # JSON string of examples
    saved = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daily_done = db.Column(db.Integer, default=0)
    daily_date = db.Column(db.String(20), unique=True)  # Date string
