# English Learning Lab

A Flask-based English learning application with AI-powered conversation, grammar checking, vocabulary building, and flashcard review.

## Features

- **AI Conversation**: Practice spoken English with voice input and text-to-speech
- **Grammar Checker**: Get inline corrections with explanations for your writing
- **Vocabulary Builder**: Look up words with definitions and save to your library
- **Flashcards**: Spaced repetition system for reviewing grammar errors and vocabulary

## Architecture

Flask MVC architecture with:
- **Models**: SQLite database (Flashcard, Vocabulary, ChatMessage, UserProgress)
- **Views**: Jinja2 templates (base, conversation, grammar, vocabulary, flashcards)
- **Controllers**: Flask routes with REST API endpoints
- **AI Integration**: Direct Gemini API calls via google-generativeai library

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env` and add:
```
GEMINI_API_KEY=your-gemini-api-key-here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Run the Application

```bash
python app.py
```

The app will be available at http://localhost:5000

## Data Migration

If you have existing data from the HTML/JS version (localStorage), you can migrate it:

1. Open the old `index.html` in your browser
2. Open browser console (F12) and run:
```javascript
copy(JSON.stringify({
  flashcards: JSON.parse(localStorage.getItem('flashcards')||'[]'),
  vocabulary: JSON.parse(localStorage.getItem('vocab')||'[]'),
  daily_done: localStorage.getItem('daily_done'),
  daily_date: localStorage.getItem('daily_date')
}))
```
3. Paste the copied JSON into a file (e.g., `export.json`)
4. Run the migration script:
```bash
python migrations/import_localstorage.py export.json
```

## Project Structure

```
english_lab/
├── app.py                 # Flask application & routes
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── models/                # Database models
│   ├── database.py
│   └── schemas.py
├── services/              # AI services
│   └── gemini_service.py
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── conversation.html
│   ├── grammar.html
│   ├── vocabulary.html
│   └── flashcards.html
├── static/                # Static files
│   ├── css/style.css
│   └── js/main.js
└── migrations/            # Data migration scripts
    └── import_localstorage.py
```

## API Endpoints

- `POST /api/chat` - Send message to AI conversation
- `POST /api/grammar` - Check grammar
- `POST /api/vocabulary` - Look up or save vocabulary
- `GET /api/vocabulary` - Get saved vocabulary
- `DELETE /api/vocabulary` - Delete vocabulary word
- `GET /api/flashcards` - Get flashcards
- `POST /api/flashcards` - Save flashcard
- `DELETE /api/flashcards/<id>` - Delete flashcard
- `GET /api/progress` - Get daily progress
- `POST /api/progress` - Update daily progress
- `GET /api/export` - Export all data as JSON

## Future Enhancements

- User authentication and multi-user support
- Cloud database integration (PostgreSQL)
- More advanced spaced repetition algorithm
- Export to Anki format
- Mobile app version