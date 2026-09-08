import json
from sqlalchemy import text
from app.db import engine

def import_bookmarks(filename):
    with open(filename) as handle:
        bookmarks = json.load(handle)
    with engine.connect() as connection:
        for bookmark in bookmarks:
            connection.execute(text("INSERT INTO bookmarks (url, title) VALUES (:url, :title)"), bookmark)
    return len(bookmarks)
