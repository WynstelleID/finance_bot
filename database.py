# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
import sys

# Gunakan DATABASE_URL dari environment variable yang disediakan Railway.
# Jika tidak ada (misalnya, saat development lokal tanpa Railway), fallback ke SQLite lokal.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///finance.db")

# Print database URL for debugging (without password if it's PostgreSQL)
if DATABASE_URL.startswith("postgresql://"):
    # Hide password from logs for security
    import re
    safe_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', DATABASE_URL)
    print(f"Attempting to connect to PostgreSQL database: {safe_url}")
elif DATABASE_URL.startswith("sqlite://"):
    print(f"Using SQLite database: {DATABASE_URL}")
else:
    print(f"Using database: {DATABASE_URL}")

def create_database_engine(database_url, retry_with_sqlite=True):
    """
    Create database engine with fallback to SQLite if PostgreSQL fails.
    """
    try:
        # Membuat engine SQLAlchemy dengan connection pooling yang lebih robust untuk PostgreSQL
        if database_url.startswith("postgresql://"):
            engine = create_engine(
                database_url, 
                echo=False,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=300,    # Recycle connections every 5 minutes
                connect_args={"connect_timeout": 10}  # 10 second timeout
            )
        else:
            engine = create_engine(database_url, echo=False)
        
        # Test the connection
        with engine.connect() as conn:
            print("Database connection successful!")
            return engine
            
    except Exception as e:
        print(f"Database connection failed: {e}")
        
        if "postgres.railway.internal" in str(e) and retry_with_sqlite:
            print("ERROR: Railway PostgreSQL database is not properly connected.")
            print("Please check your Railway dashboard to ensure:")
            print("1. PostgreSQL service is added to your project")
            print("2. Database service is linked to your application")
            print("3. DATABASE_URL environment variable is properly set")
            print("\nFalling back to SQLite for now...")
            
            # Fallback to SQLite
            fallback_url = "sqlite:///finance.db"
            return create_database_engine(fallback_url, retry_with_sqlite=False)
        else:
            print(f"DATABASE_URL: {database_url}")
            raise

# Create the engine with fallback mechanism
engine = create_database_engine(DATABASE_URL)

# Base untuk model deklaratif
Base = declarative_base()

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session untuk sesi thread-local
db_session = scoped_session(SessionLocal)

def init_db():
    """
    Inisialisasi database: membuat semua tabel yang didefinisikan.
    Ini harus dipanggil sekali saat aplikasi dimulai.
    """
    try:
        import models # Impor model di sini untuk memastikan mereka terdaftar dengan Base
        Base.metadata.create_all(bind=engine)
        print(f"Database initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise

def get_db():
    """
    Fungsi untuk mendapatkan sesi database.
    Memastikan sesi ditutup dengan benar setelah digunakan.
    """
    session = db_session()
    try:
        yield session
    finally:
        session.close()

if __name__ == '__main__':
    # Blok ini memungkinkan Anda menjalankan `python database.py` secara lokal
    # untuk menginisialisasi database (akan menggunakan SQLite jika tidak ada DATABASE_URL).
    init_db()
    print("Database initialization complete.")
    