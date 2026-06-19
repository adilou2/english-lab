from flask import Flask, render_template, request, jsonify, send_file
from config import Config
from models import db, Flashcard, Vocabulary, ChatMessage, UserProgress
from services.gemini_service import get_gemini_service
import json
from datetime import datetime
import os
import asyncio

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/conversation')
def conversation():
    return render_template('conversation.html')

@app.route('/grammar')
def grammar():
    return render_template('grammar.html')

@app.route('/vocabulary')
def vocabulary():
    return render_template('vocabulary.html')

@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html')

# API Routes
@app.route('/api/chat', methods=['POST'])
def chat():
    print("=== /api/chat called ===")
    data = request.json
    user_message = data.get('message')
    chat_history = data.get('history', [])
    print(f"Message: {user_message}")
    print(f"History length: {len(chat_history)}")
    
    # Save user message
    chat_msg = ChatMessage(role='user', content=user_message)
    db.session.add(chat_msg)
    db.session.commit()
    
    # Call Gemini API for response
    try:
        print(f"Attempting to get Gemini service...")
        gemini = get_gemini_service()
        print(f"Gemini service obtained, calling chat_conversation...")
        response = asyncio.run(gemini.chat_conversation(chat_history, user_message))
        print(f"Response received: {response}")
        
        # Save assistant message
        assistant_msg = ChatMessage(role='assistant', content=response['reply'])
        db.session.add(assistant_msg)
        db.session.commit()
        
        # Save grammar errors to flashcards
        if response.get('errors'):
            for error in response['errors']:
                card = Flashcard(
                    id=datetime.now().timestamp(),
                    type='grammar',
                    front=error['original'],
                    back=error['correction'],
                    explanation=error['explanation'],
                    source='conversation'
                )
                db.session.add(card)
            db.session.commit()
        
        return jsonify(response)
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({
            'reply': 'Sorry, something went wrong. Please try again.',
            'errors': []
        })

@app.route('/api/grammar', methods=['POST'])
def check_grammar():
    data = request.json
    text = data.get('text')
    
    # Call Gemini API for grammar check
    try:
        gemini = get_gemini_service()
        response = asyncio.run(gemini.check_grammar(text))
        return jsonify(response)
    except Exception as e:
        print(f"Error in grammar check: {e}")
        return jsonify({
            'annotated': text,
            'errors': []
        })

@app.route('/api/vocabulary', methods=['POST'])
def lookup_vocabulary():
    data = request.json
    word = data.get('word')
    
    # Check if it's a save operation (already looked up)
    if data.get('pos') and data.get('definition'):
        # Save to database
        existing = Vocabulary.query.filter_by(word=word).first()
        if not existing:
            vocab = Vocabulary(
                word=word,
                pos=data.get('pos'),
                definition=data.get('definition'),
                examples=json.dumps(data.get('examples', []))
            )
            db.session.add(vocab)
            db.session.commit()
        return jsonify({'success': True})
    
    # Call Gemini API for word lookup
    try:
        gemini = get_gemini_service()
        response = asyncio.run(gemini.lookup_vocabulary(word))
        return jsonify(response)
    except Exception as e:
        print(f"Error in vocabulary lookup: {e}")
        return jsonify({
            'word': word,
            'pos': 'unknown',
            'definition': 'Error looking up word.',
            'examples': []
        })

@app.route('/api/vocabulary', methods=['GET'])
def get_vocabulary():
    words = Vocabulary.query.order_by(Vocabulary.saved.desc()).all()
    return jsonify([{
        'id': w.id,
        'word': w.word,
        'pos': w.pos,
        'definition': w.definition,
        'examples': json.loads(w.examples) if w.examples else []
    } for w in words])

@app.route('/api/vocabulary', methods=['DELETE'])
def delete_vocabulary():
    data = request.json
    word_id = data.get('id')
    word = Vocabulary.query.get(word_id)
    if word:
        db.session.delete(word)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    cards = Flashcard.query.all()
    return jsonify([{
        'id': c.id,
        'type': c.type,
        'front': c.front,
        'back': c.back,
        'explanation': c.explanation,
        'source': c.source
    } for c in cards])

@app.route('/api/flashcards', methods=['POST'])
def save_flashcard():
    data = request.json
    card = Flashcard(
        id=data.get('id', datetime.now().timestamp()),
        type=data.get('type'),
        front=data.get('front'),
        back=data.get('back'),
        explanation=data.get('explanation'),
        source=data.get('source')
    )
    db.session.add(card)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/flashcards/<float:card_id>', methods=['DELETE'])
def delete_flashcard(card_id):
    card = Flashcard.query.get(card_id)
    if card:
        db.session.delete(card)
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/progress', methods=['GET'])
def get_progress():
    today = datetime.now().strftime('%Y-%m-%d')
    progress = UserProgress.query.filter_by(daily_date=today).first()
    if not progress:
        progress = UserProgress(daily_done=0, daily_date=today)
        db.session.add(progress)
        db.session.commit()
    return jsonify({'daily_done': progress.daily_done, 'daily_date': progress.daily_date})

@app.route('/api/progress', methods=['POST'])
def update_progress():
    data = request.json
    today = datetime.now().strftime('%Y-%m-%d')
    progress = UserProgress.query.filter_by(daily_date=today).first()
    if progress:
        progress.daily_done = data.get('daily_done', 0)
    else:
        progress = UserProgress(daily_done=data.get('daily_done', 0), daily_date=today)
        db.session.add(progress)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/export')
def export_data():
    data = {
        'flashcards': [{
            'id': c.id,
            'type': c.type,
            'front': c.front,
            'back': c.back,
            'explanation': c.explanation,
            'source': c.source,
            'added': c.added.isoformat()
        } for c in Flashcard.query.all()],
        'vocabulary': [{
            'id': w.id,
            'word': w.word,
            'pos': w.pos,
            'definition': w.definition,
            'examples': json.loads(w.examples) if w.examples else [],
            'saved': w.saved.isoformat()
        } for w in Vocabulary.query.all()],
        'exportedAt': datetime.now().isoformat()
    }
    
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(data, temp_file, indent=2)
    temp_file.close()
    
    return send_file(temp_file.name, as_attachment=True, download_name='english-lab-data.json')

if __name__ == '__main__':
    app.run(debug=True)
