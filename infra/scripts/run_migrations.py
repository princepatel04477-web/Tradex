"""Run SQL database migrations against Neon PostgreSQL instance."""

from pathlib import Path
import psycopg

DIRECT_URL = "postgresql://neondb_owner:npg_HvmuAp73ZheE@ep-summer-fire-azhbgrge.c-3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

MIGRATION_FILES = [
    "0001_initial_schema.sql",
    "0002_rls_policies.sql",
    "0003_seed_currency_pairs.sql",
    "0004_users_and_auth.sql",
]


def run():
    print(f"Connecting to Neon PostgreSQL...")
    conn = psycopg.connect(DIRECT_URL, autocommit=True)
    cursor = conn.cursor()
    print("Connected successfully!")

    # Check pgvector extension
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        print("Vector and UUID extensions enabled.")
    except Exception as e:
        print(f"Notice on extensions: {e}")

    for filename in MIGRATION_FILES:
        filepath = MIGRATIONS_DIR / filename
        if not filepath.exists():
            print(f"File not found: {filepath}")
            continue
        print(f"\nApplying migration: {filename}...")
        sql = filepath.read_text(encoding="utf-8")
        try:
            cursor.execute(sql)
            print(f"  Applied {filename} successfully.")
        except Exception as e:
            print(f"  Notice/Error on {filename}: {e}")

    # Verify tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cursor.fetchall()]
    print(f"\nSuccessfully verified {len(tables)} tables on Neon DB:")
    for t in tables:
        print(f"  - {t}")

    # Verify seed data
    cursor.execute("SELECT symbol, base_currency, quote_currency, pip_decimal_places, category FROM currency_pairs ORDER BY created_at;")
    pairs = cursor.fetchall()
    print(f"\nVerified {len(pairs)} Seeded Currency Pairs:")
    for p in pairs:
        print(f"  {p[0]} ({p[1]}/{p[2]}) - {p[3]} decimals [{p[4]}]")

    # Verify signal weights config
    cursor.execute("SELECT indicator_name, weight, description FROM signal_weights_config ORDER BY id;")
    weights = cursor.fetchall()
    print(f"\nVerified {len(weights)} Signal Weights (AI-3.3):")
    for w in weights:
        print(f"  {w[0]}: weight={w[1]} ({w[2]})")

    conn.close()


if __name__ == "__main__":
    run()
