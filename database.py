# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# Define the path for the SQLite database file.
# It will be created in the current working directory.
# DATABASE_FILE = os.path.join(os.getcwd(), 'finance.db')
# DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Gunakan DATABASE_URL dari environment variable yang disediakan Railway,
# dengan fallback ke SQLite lokal jika variabel tidak ada (untuk dev lokal).
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///finance.db")

# Create the SQLAlchemy engine. echo=True enables logging of SQL statements.
engine = create_engine(DATABASE_URL, echo=False)

# Create a base class for declarative models.
Base = declarative_base()

# Configure a sessionmaker for creating new session objects.
# autoflush=False means changes are not flushed to the DB until commit or explicit flush.
# autocommit=False means transactions are not automatically committed after each operation.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session for thread-local sessions.
# This ensures that each request/thread gets its own session instance,
# preventing issues with concurrent access.
db_session = scoped_session(SessionLocal)

def init_db():
    """
    Initializes the database by creating all defined tables.
    This should be called once when the application starts.
    """
    import models # Import models here to ensure they are registered with Base
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DATABASE_FILE}")

def get_db():
    """
    Dependency function to get a database session.
    This is typically used in Flask route handlers or other functions
    that need to interact with the database.
    It yields the session and ensures it's closed properly afterwards.
    """
    session = db_session()
    try:
        yield session
    finally:
        session.close() # Ensure the session is closed after use

if __name__ == '__main__':
    # This block allows you to run `python database.py` to initialize the database
    # without running the full Flask application.
    init_db()
    print("Database initialization complete.")
