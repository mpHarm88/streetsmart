# DOCS: https://fastapi.tiangolo.com/#typer-the-fastapi-of-clis
# run app in terminal with "uvicorn main:app --reload"

from fastapi import FastAPI
import os
from dotenv import load_dotenv
import psycopg2
from modules import carbon_function

load_dotenv()

#Load credentials from .env
name = os.getenv("DB_NAME")
password = os.getenv("DB_PW")
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")

# Create connection to heroku database
pg_conn = psycopg2.connect(dbname=name, user=user,
                        password=password, host=host)

app = FastAPI()

@app.get("/")
def read_root():
    return{"pred": 1000}

@app.get("/items/{model}")
def read_item(model: str, q: str = None):
    "Return All Models"

    return {"pred": item_id, "q": q}
