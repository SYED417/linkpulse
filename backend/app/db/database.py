import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Read the .env file and load its values into environment variables.
load_dotenv()

# Pull the connection string we defined in backend/.env
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not set. Check your backend/.env file.")

# The engine is the core connection to PostgreSQL. It manages a pool of
# connections that get reused across requests.
engine = create_engine(DATABASE_URL)

# A session is a single "conversation" with the database (one unit of work).
# SessionLocal is a factory: calling SessionLocal() gives us a new session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all our ORM models. SQLAlchemy uses it to
# keep track of every table/model we define.
Base = declarative_base()


# FastAPI dependency: opens a session for one request, then guarantees it
# is closed afterwards, even if an error happens.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
