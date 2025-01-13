import os
import sqlite3

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


class TextToSQL:
    def __init__(self, openai_client, db_path: str):
        self.client = openai_client
        self.db_path = db_path
        self.table_schemas = self._load_table_schemas()

    def _load_table_schemas(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        schemas = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            schemas.append(
                {
                    "table_name": table_name,
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "nullable": not col[3],
                            "primary_key": bool(col[5]),
                        }
                        for col in columns
                    ],
                }
            )

        conn.close()
        return schemas

    def _determine_table_from_query(self, query: str) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a database expert. Respond only with the relevant table name, nothing else.",
                },
                {
                    "role": "user",
                    "content": f"""Given these database tables and their schemas:

{self.table_schemas}

For this user query: "{query}"

Which table is most relevant? Respond with just the table name.""",
                },
            ],
        )

        return completion.choices[0].message.content.strip()

    def _generate_sql_from_query(self, query: str, table_name: str) -> str:
        """Generate SQL query for the given natural language query."""
        table_schema = next((s for s in self.table_schemas if s["table_name"] == table_name), None)
        if not table_schema:
            raise ValueError(f"Table '{table_name}' not found in database")

        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a SQL expert. Return only the raw SQL query without any markdown formatting, quotes, or backticks.",
                },
                {
                    "role": "user",
                    "content": f"""Given this table schema:

{table_schema}

Convert this user query into SQL: "{query}"

Return only the raw SQL query without any markdown formatting, quotes, or backticks.""",
                },
            ],
        )

        sql_query = completion.choices[0].message.content.strip()

        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        if sql_query.endswith(";"):
            sql_query = sql_query[:-1]

        return sql_query

    def execute_query(self, user_query: str) -> list[tuple]:
        table_name = self._determine_table_from_query(user_query)
        print(f"Selected table: {table_name}")

        sql_query = self._generate_sql_from_query(user_query, table_name)
        print(f"Generated SQL: {sql_query}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()

        return results


def setup_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        product_name TEXT,
        quantity INTEGER,
        price REAL,
        sale_date DATE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        salary REAL,
        hire_date DATE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        location TEXT,
        join_date DATE
    )""")

    cursor.executemany(
        "INSERT INTO sales (product_name, quantity, price, sale_date) VALUES (?, ?, ?, ?)",
        [
            ("Laptop", 5, 999.99, "2024-01-15"),
            ("Mouse", 10, 29.99, "2024-01-16"),
            ("Keyboard", 7, 79.99, "2024-01-17"),
        ],
    )

    cursor.executemany(
        "INSERT INTO employees (name, department, salary, hire_date) VALUES (?, ?, ?, ?)",
        [
            ("John Doe", "Engineering", 85000, "2023-03-15"),
            ("Jane Smith", "Sales", 75000, "2023-04-01"),
            ("Bob Wilson", "Marketing", 70000, "2023-05-10"),
        ],
    )

    cursor.executemany(
        "INSERT INTO customers (name, email, location, join_date) VALUES (?, ?, ?, ?)",
        [
            ("Alice Brown", "alice@email.com", "New York", "2023-01-15"),
            ("Charlie Davis", "charlie@email.com", "Los Angeles", "2023-02-01"),
            ("Eve Wilson", "eve@email.com", "Chicago", "2023-02-15"),
        ],
    )

    conn.commit()
    conn.close()


def cleanup_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_path = "test.db"
    openai_api_key = os.environ.get("OPENAI_API_KEY_91")

    cleanup_database(db_path)
    setup_database(db_path)

    openai_client = OpenAI(api_key=openai_api_key)
    converter = TextToSQL(openai_client, db_path)

    test_queries = [
        "What are all product names and their prices?",
        "Show me employees in the Engineering department",
        "List all customers from New York",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            results = converter.execute_query(query)
            print("Results:", results)
        except Exception as e:
            print(f"Error: {e}")
