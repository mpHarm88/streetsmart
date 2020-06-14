from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy.orm import sessionmaker

load_dotenv()

user = os.environ["DB_USER_AWS"]
pw = os.environ["DB_PW_AWS"]
host = os.environ["DB_HOST_AWS"]
name = os.environ["DB_NAME_AWS"]
port = os.environ["DB_PORT_AWS"]

# postgresql+psycopg2://user:password@host:port/dbname
SQLALCHEMY_DATABASE_URL = f"postgresql://{user}:{pw}@{host}:{port}/{name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Crate a session factory that is bound to the engine
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
    )

Base = declarative_base()