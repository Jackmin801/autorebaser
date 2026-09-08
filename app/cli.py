import argparse
import json
from app.db import initialize, add_bookmark, list_bookmarks

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("url")
    add.add_argument("title")
    sub.add_parser("list")
    # Feature command registration
    args = parser.parse_args()
    initialize()
    if args.action == "add":
        add_bookmark(args.url, args.title)
        print(json.dumps({"saved": 1}))
    elif args.action == "list":
        print(json.dumps(list_bookmarks()))
    # Feature command dispatch

if __name__ == "__main__":
    main()
