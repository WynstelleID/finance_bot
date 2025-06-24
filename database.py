# -*- coding: utf-8 -*-
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
import sys
import time

# Debug environment variables for Railway
print("=== DATABASE CONFIGURATION DEBUG ===")
railway_vars = [key for key in os.environ.keys() if 'DATABASE' in key or 'POSTGRES' in key or 'RAILWAY' in key]
if railway_vars:
    print("Found Railway/Database environment variables:")
    for var in railway_vars:
        if 'PASSWORD' in var or 'PASS' in var:
            print(f"  {var}: ***HIDDEN***")
        else:
            print(f"  {var}: {os.environ[var]}")
else:
    print("No Railway/Database environment variables found")
print("=====================================")

# Use DATABASE_URL from environment variable provided by Railway.
# If not available (e.g., during local development without Railway), fallback to local SQLite.
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
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Create SQLAlchemy engine with robust connection pooling for PostgreSQL
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
            
            # Test the connection more thoroughly
            try:
                with engine.connect() as conn:
                    # Try a simple query to ensure the connection actually works
                    if database_url.startswith("postgresql://"):
                        from sqlalchemy import text
                        conn.execute(text("SELECT 1"))
                    print("Database connection successful!")
                    return engine
            except Exception as conn_error:
                print(f"Connection test failed (attempt {attempt + 1}/{max_retries}): {conn_error}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise conn_error
                
        except Exception as e:
            print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                if "postgres.railway.internal" in str(e) or "Name or service not known" in str(e):
                    print("Railway private networking issue detected, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            
            # If all retries failed, try fallback
            if ("postgres.railway.internal" in str(e) or "Name or service not known" in str(e)) and retry_with_sqlite:
                print("ERROR: Railway PostgreSQL database is not properly connected after retries.")
                print("Please check your Railway dashboard to ensure:")
                print("1. PostgreSQL service is added to your project")
                print("2. Database service is linked to your application")
                print("3. DATABASE_URL environment variable is properly set")
                print("4. Add ENABLE_ALPINE_PRIVATE_NETWORKING=true if using Alpine containers")
                print("5. Ensure you have a 'sleep 3' in your start command")
                print("\nFalling back to SQLite for now...")
                
                # Fallback to SQLite
                fallback_url = "sqlite:///finance.db"
                return create_database_engine(fallback_url, retry_with_sqlite=False)
            else:
                print(f"DATABASE_URL: {database_url}")
                raise

# Create the engine with fallback mechanism
engine = create_database_engine(DATABASE_URL)

# Base for declarative models
Base = declarative_base()

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread-local sessions
db_session = scoped_session(SessionLocal)

def init_db():
    """
    Initialize database: create all defined tables.
    This should be called once when the application starts.
    """
    global engine, SessionLocal, db_session
    
    try:
        import models # Import models here to ensure they are registered with Base
        Base.metadata.create_all(bind=engine)
        print(f"Database initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize database with current engine: {e}")
        
        # If we get a postgres.railway.internal error, try to recreate engine with fallback
        if "postgres.railway.internal" in str(e):
            print("Attempting to recreate database engine with fallback...")
            try:
                # Try to recreate the engine with fallback
                original_url = os.environ.get("DATABASE_URL", "sqlite:///finance.db")
                engine = create_database_engine(original_url)
                
                # Update the session makers to use the new engine
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                db_session = scoped_session(SessionLocal)
                
                # Try to create tables again
                Base.metadata.create_all(bind=engine)
                print(f"Database initialized successfully with fallback!")
                return
                
            except Exception as fallback_error:
                print(f"Fallback initialization also failed: {fallback_error}")
                raise
        else:
            raise

def get_db():
    """
    Function to get database session.
    Ensures session is properly closed after use.
    """
    session = db_session()
    try:
        yield session
    finally:
        session.close()

if __name__ == '__main__':
    # This block allows you to run `python database.py` locally
    # to initialize the database (will use SQLite if no DATABASE_URL).
    init_db()
    print("Database initialization complete.")
    