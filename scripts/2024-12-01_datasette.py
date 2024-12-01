import argparse
import socket
import subprocess
import sys
from pathlib import Path


def run_datasette(db_path, host="0.0.0.0", port=8001):
    if not Path(db_path).exists():
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    if not is_port_available(port):
        print(f"Error: Port {port} is already in use")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "datasette",
        "serve",
        db_path,
        "--host",
        host,
        "--port",
        str(port),
        "--cors",  # enable CORS for API access
    ]

    print("\nStarting Datasette server...")
    print(f"Database: {db_path}")
    print(f"URL: http://{host}:{port}")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down Datasette server...")
    except Exception as e:
        print(f"Error running Datasette: {e}")
        sys.exit(1)


def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            return True
        except OSError:
            return False


def main():
    parser = argparse.ArgumentParser(description="Deploy SQLite database with Datasette")
    parser.add_argument("db_path", help="Path to SQLite database file")
    parser.add_argument("--host", default="localhost", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="Port to run on (default: 8001)")

    args = parser.parse_args()

    run_datasette(args.db_path, host=args.host, port=args.port)


if __name__ == "__main__":
    main()  # NOTE: python script.py database.db --host localhost --port 8080
