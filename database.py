# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# Gunakan DATABASE_URL dari environment variable yang disediakan Railway.
# Jika tidak ada (misalnya, saat development lokal tanpa Railway), fallback ke SQLite lokal.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///finance.db")

# Membuat engine SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)

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
        import models # Impor model di sini untuk memastikan mereka terdaftar dengan Base
        Base.metadata.create_all(bind=engine)
        print(f"Database initialized using URL: {DATABASE_URL}")

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
    