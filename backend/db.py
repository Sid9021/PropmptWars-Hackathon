import duckdb
import os
from contextlib import contextmanager

DB_FILE = os.getenv("DUCKDB_FILE", "recover.duckdb")

def init_db():
    conn = duckdb.connect(DB_FILE)

    # Create Credentials table (login info, separate from recovery profile)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS credentials (
        id VARCHAR PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR NOT NULL,
        role VARCHAR DEFAULT 'user',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create Users table (recovery profile)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        substance_history VARCHAR,
        triggers VARCHAR,
        support_network VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create Logs table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR,
        event_type VARCHAR,
        sentiment VARCHAR,
        craving_intensity INTEGER,
        notes VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create Emergencies table (real-time alert from mobile users)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS emergencies (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR,
        user_name VARCHAR,
        last_message VARCHAR,
        is_resolved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.close()


@contextmanager
def get_db():
    conn = duckdb.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
