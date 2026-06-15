import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Pull the pieces out securely
DB_USER = os.getenv("AZURE_DB_USER")
DB_PASSWORD = os.getenv("AZURE_DB_PASSWORD")
DB_HOST = os.getenv("AZURE_DB_HOST")
DB_NAME = os.getenv("AZURE_DB_NAME")

# Assemble the connection string dynamically using f-strings
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?sslmode=require"
# 2. Create the engine
# (Note: We removed the SQLite-specific 'connect_args={"check_same_thread": False}')
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. Create the Session factory (Your get_db dependency uses this)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. The base catalog for your tables
Base = declarative_base()
