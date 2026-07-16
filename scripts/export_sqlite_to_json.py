"""Export local SQLite data to a JSON file for migration to Postgres."""
import json
import os
import sys
from datetime import datetime

# Allow importing models when the script is run from the scripts directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import ChatMessage, Flashcard, UserProgress, Vocabulary, db


def serialize_row(row):
    """Convert a SQLAlchemy ORM instance to a JSON-serializable dict."""
    data = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        # Vocabulary.examples is stored as a JSON string; parse it.
        if col.name == 'examples' and isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        data[col.name] = value
    return data


def main():
    sqlite_path = os.path.join(PROJECT_ROOT, 'instance', 'english_lab.db')
    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite file not found: {sqlite_path}")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{sqlite_path}")
    db.metadata.create_all(engine)

    export = {}
    with Session(engine) as session:
        for model in [Flashcard, Vocabulary, ChatMessage, UserProgress]:
            rows = session.scalars(select(model)).all()
            export[model.__tablename__] = [serialize_row(row) for row in rows]

    output_path = os.path.join(PROJECT_ROOT, 'instance', 'export.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, ensure_ascii=False)

    print(f"Exported {sum(len(v) for v in export.values())} rows to {output_path}")


if __name__ == '__main__':
    main()
