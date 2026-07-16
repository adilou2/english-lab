"""Import JSON data exported by export_sqlite_to_json.py into a Postgres database."""
import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime

# Allow importing models when the script is run from the scripts directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, make_transient

from models import ChatMessage, Flashcard, UserProgress, Vocabulary, db


def _postgres_driver():
    if importlib.util.find_spec('psycopg2'):
        return 'postgresql'
    if importlib.util.find_spec('psycopg'):
        return 'postgresql+psycopg'
    return 'postgresql'


def parse_value(model, column, value):
    """Convert JSON values back to Python values for the given model column."""
    if value is None:
        return None
    if column in ('added', 'saved', 'timestamp') and isinstance(value, str):
        return datetime.fromisoformat(value)
    if column == 'examples' and isinstance(value, list):
        return json.dumps(value)
    return value


def import_data(json_path, pg_url):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Normalize URL for the available driver and Render's postgres:// prefix.
    if pg_url.startswith('postgres://'):
        pg_url = pg_url.replace('postgres://', f'{_postgres_driver()}://', 1)
    elif pg_url.startswith('postgresql://'):
        driver = _postgres_driver()
        if driver != 'postgresql':
            pg_url = pg_url.replace('postgresql://', f'{driver}://', 1)

    # Render requires SSL for external Postgres connections.
    if pg_url.startswith(('postgres://', 'postgresql://')) and 'sslmode=' not in pg_url:
        separator = '&' if '?' in pg_url else '?'
        pg_url += f'{separator}sslmode=require'

    engine = create_engine(pg_url)
    db.metadata.create_all(engine)

    table_order = [
        ('flashcard', Flashcard),
        ('vocabulary', Vocabulary),
        ('chat_message', ChatMessage),
        ('user_progress', UserProgress),
    ]

    counts = {}
    with Session(engine) as session:
        for table_name, model in table_order:
            rows = data.get(table_name, [])
            for row in rows:
                obj = model(
                    **{
                        col.name: parse_value(model, col.name, row.get(col.name))
                        for col in model.__table__.columns
                    }
                )
                make_transient(obj)
                session.add(obj)
            counts[table_name] = len(rows)
        session.commit()

    # Reset Postgres serial/identity sequences.
    with Session(engine) as session:
        for _, model in table_order:
            if model is Flashcard:
                continue
            try:
                seq_name = session.scalar(
                    text('SELECT pg_get_serial_sequence(:table, :col)')
                    .bindparams(table=model.__tablename__, col='id')
                )
                if seq_name:
                    max_id = session.scalar(
                        text(f'SELECT MAX(id) FROM {model.__tablename__}')
                    )
                    if max_id:
                        session.execute(
                            text('SELECT setval(:seq, :val, true)'),
                            {'seq': seq_name, 'val': max_id},
                        )
                        session.commit()
            except Exception as e:
                print(f'  sequence reset skipped for {model.__tablename__}: {e}')

    print('Import complete. Inserted:')
    for name, count in counts.items():
        print(f'  {name}: {count}')


def main():
    parser = argparse.ArgumentParser(
        description='Import JSON data into the Postgres database.'
    )
    parser.add_argument(
        'json',
        default='instance/import.json',
        nargs='?',
        help='Path to the JSON file exported by export_sqlite_to_json.py',
    )
    parser.add_argument(
        '--pg-url',
        default=os.environ.get('DATABASE_URL') or os.environ.get('PG_DATABASE_URL'),
        help='Target Postgres URL (defaults to DATABASE_URL env var)',
    )
    args = parser.parse_args()

    if not args.pg_url:
        print('ERROR: No Postgres URL. Set DATABASE_URL or pass --pg-url.')
        sys.exit(1)

    import_data(args.json, args.pg_url)


if __name__ == '__main__':
    main()
