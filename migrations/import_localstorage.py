"""
Import localStorage data from JSON export to SQLite database.
Run this script after exporting data from the existing HTML app.
"""
import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Flashcard, Vocabulary, ChatMessage, UserProgress

def import_localstorage(json_file_path):
    """Import data from localStorage JSON export to SQLite database."""
    
    with app.app_context():
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Import flashcards
        flashcards = data.get('flashcards', [])
        for fc in flashcards:
            # Check if flashcard already exists by id
            existing = Flashcard.query.get(fc.get('id'))
            if not existing:
                card = Flashcard(
                    id=fc.get('id'),
                    type=fc.get('type'),
                    front=fc.get('front'),
                    back=fc.get('back'),
                    explanation=fc.get('explanation'),
                    source=fc.get('source'),
                    added=datetime.fromisoformat(fc.get('added', datetime.now().isoformat()))
                )
                db.session.add(card)
                print(f"Imported flashcard: {fc.get('front')[:30]}...")
            else:
                print(f"Flashcard already exists: {fc.get('front')[:30]}...")
        
        # Import vocabulary
        vocabulary = data.get('vocabulary', [])
        for vocab in vocabulary:
            # Check if word already exists
            existing = Vocabulary.query.filter_by(word=vocab.get('word')).first()
            if not existing:
                word = Vocabulary(
                    word=vocab.get('word'),
                    pos=vocab.get('pos'),
                    definition=vocab.get('definition'),
                    examples=json.dumps(vocab.get('examples', [])),
                    saved=datetime.fromisoformat(vocab.get('saved', datetime.now().isoformat()))
                )
                db.session.add(word)
                print(f"Imported vocabulary: {vocab.get('word')}")
            else:
                print(f"Vocabulary already exists: {vocab.get('word')}")
        
        # Import user progress if available
        if 'daily_done' in data or 'daily_date' in data:
            today = data.get('daily_date', datetime.now().strftime('%Y-%m-%d'))
            existing = UserProgress.query.filter_by(daily_date=today).first()
            if not existing:
                progress = UserProgress(
                    daily_done=data.get('daily_done', 0),
                    daily_date=today
                )
                db.session.add(progress)
                print(f"Imported progress: {data.get('daily_done')} / 10")
            else:
                print(f"Progress already exists for {today}")
        
        # Commit all changes
        db.session.commit()
        print("\nImport completed successfully!")
        print(f"Imported {len(flashcards)} flashcards")
        print(f"Imported {len(vocabulary)} vocabulary words")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python import_localstorage.py <path_to_json_export>")
        print("\nTo export data from the existing HTML app:")
        print("1. Open the existing index.html in your browser")
        print("2. Open browser console (F12)")
        print("3. Run: copy(JSON.stringify({flashcards: JSON.parse(localStorage.getItem('flashcards')||'[]'), vocabulary: JSON.parse(localStorage.getItem('vocab')||'[]'), daily_done: localStorage.getItem('daily_done'), daily_date: localStorage.getItem('daily_date')}))")
        print("4. Paste the copied JSON into a file")
        print("5. Run this script with that file path")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    import_localstorage(json_file)
