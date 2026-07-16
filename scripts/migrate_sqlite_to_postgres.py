"""Migrate data from local SQLite instance/english_lab.db to a Render Postgres database."""
import argparse
import importlib.util
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, make_transient

# Load local .env so the user can use PG_DATABASE_URL or DATABASE_URL.
load_dotenv()

# Allow importing models when the script is run from the scripts directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import models after Flask-SQLAlchemy has had a chance to define the mapping.
from models import ChatMessage, Flashcard, UserProgress, Vocabulary, db


def _postgres_driver() -> str:
    """Return the SQLAlchemy Postgres driver to use based on installed packages."""
    if importlib.util.find_spec('psycopg2'):
        return 'postgresql'
    if importlib.util.find_spec('psycopg'):
        return 'postgresql+psycopg'
    return 'postgresql'


def sqlite_url(path: str) -> str:
    """Return an absolute sqlite:///<path> URL for the given SQLite file."""
    absolute = os.path.abspath(path).replace("\\", "/")
    return f"sqlite:///{absolute}"


def migrate_tables(source_engine, target_engine, dry_run=False):
    """Copy rows from all known tables, then fix Postgres serial/identity sequences."""
    table_order = [Flashcard, Vocabulary, ChatMessage, UserProgress]

    # Ensure target tables exist (idempotent with existing Render deploy).
    db.metadata.create_all(target_engine)

    with Session(source_engine) as source, Session(target_engine) as target:
        counts = {}
        for model in table_order:
            rows = source.scalars(select(model)).all()
            for row in rows:
                make_transient(row)
                target.add(row)
            counts[model.__tablename__] = len(rows)
        if dry_run:
            print("DRY RUN - not committing. Would copy:")
            for name, count in counts.items():
                print(f"  {name}: {count}")
            target.rollback()
            return
        target.commit()

    # Reset Postgres serial/identity sequences so future inserts do not collide.
    with Session(target_engine) as target:
        for model in table_order:
            if model is Flashcard:
                continue
            col_name = "id"
            try:
                seq_name = target.scalar(
                    text("SELECT pg_get_serial_sequence(:table, :col)")
                    .bindparams(table=model.__tablename__, col=col_name)
                )
                if seq_name:
                    max_id = target.scalar(
                        text(f"SELECT MAX(id) FROM {model.__tablename__}")
                    )
                    if max_id:
                        target.execute(
                            text("SELECT setval(:seq, :val, true)"),
                            {"seq": seq_name, "val": max_id},
                        )
                        target.commit()
            except Exception as e:
                print(f"  sequence reset skipped for {model.__tablename__}: {e}")

    print("Migration complete. Copied:")
    for name, count in counts.items():
        print(f"  {name}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Copy english_lab.db SQLite data into a PostgreSQL database."
    )
    parser.add_argument(
        "--pg-url",
        default=os.environ.get("PG_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or "",
        help="Target Postgres connection URL (defaults to PG_DATABASE_URL env var).",
    )
    parser.add_argument(
        "--sqlite",
        default="instance/english_lab.db",
        help="Source SQLite file path (default: instance/english_lab.db).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show counts without writing to Postgres.",
    )
    args = parser.parse_args()

    if not args.pg_url:
        print(
            "ERROR: No Postgres URL provided. Set PG_DATABASE_URL or pass --pg-url."
        )
        sys.exit(1)

    pg_url = args.pg_url
    driver = _postgres_driver()
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", f"{driver}://", 1)
    elif pg_url.startswith("postgresql://") and driver != "postgresql":
        pg_url = pg_url.replace("postgresql://", f"{driver}://", 1)

    # Render requires SSL for external Postgres connections.
    if pg_url.startswith(("postgres://", "postgresql://")) and "sslmode=" not in pg_url:
        separator = "&" if "?" in pg_url else "?"
        pg_url += f"{separator}sslmode=require"

    source_engine = create_engine(sqlite_url(args.sqlite))
    target_engine = create_engine(pg_url)

    migrate_tables(source_engine, target_engine, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
