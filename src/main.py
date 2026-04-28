import sys
import traceback
from db.connection import get_connection, release_connection
from db.schema import create_tables
from igdb.sync import sync_games


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        print("Commands: sync")
        sys.exit(1)

    command = sys.argv[1]

    if command == "sync":
        conn = get_connection()
        try:
            create_tables(conn)
            sync_games()
        except Exception as e:
            print(f"Error occurred: {e}")
            traceback.print_exc()
        finally:
            release_connection(conn)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()