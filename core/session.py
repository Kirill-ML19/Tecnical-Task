import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

load_dotenv()

database_url = os.getenv('DATABASE_URL')

engine = create_engine(
    url=database_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)