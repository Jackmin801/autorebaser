import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["BOOKMARK_DB"])

def initialize():
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS bookmarks (url TEXT PRIMARY KEY, title TEXT NOT NULL)"))

def add_bookmark(url, title):
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO bookmarks (url, title) VALUES (:url, :title)"), {"url": url, "title": title})

def list_bookmarks():
    with engine.connect() as connection:
        return [dict(row._mapping) for row in connection.execute(text("SELECT url, title FROM bookmarks ORDER BY url"))]
