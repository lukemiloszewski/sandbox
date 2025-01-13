# https://github.com/asg017/sqlite-vec/issues/13

import pathlib
import sqlite3
import struct

path_to_dll = pathlib.Path("C:\\Users\\lmiloszewski\\dev_programs\\vec0.dll")
# path_to_dll = pathlib.Path("C:\\Users\\lmiloszewski\\code\\sandbox\\.venv\\Lib\\site-packages\\sqlite_vec\\vec0.dll")

db = sqlite3.connect(":memory:")
db.enable_load_extension(True)

# sqlite_vec.load(db)  # doesn't work
db.load_extension(str(path_to_dll))

db.enable_load_extension(False)


def check_sqlite_vec():
    (vec_version,) = db.execute("select vec_version()").fetchone()
    print(f"vec_version={vec_version}")


def serialize_f32(vector: list[float]) -> bytes:
    """serializes a list of floats into a compact "raw bytes" format"""
    return struct.pack("%sf" % len(vector), *vector)  # noqa: UP031


sqlite_version, vec_version = db.execute("select sqlite_version(), vec_version()").fetchone()
print(f"sqlite_version={sqlite_version}, vec_version={vec_version}")

items = [
    (1, [0.1, 0.1, 0.1, 0.1]),
    (2, [0.2, 0.2, 0.2, 0.2]),
    (3, [0.3, 0.3, 0.3, 0.3]),
    (4, [0.4, 0.4, 0.4, 0.4]),
    (5, [0.5, 0.5, 0.5, 0.5]),
]
query = [0.3, 0.3, 0.3, 0.3]

db.execute("CREATE VIRTUAL TABLE vec_items USING vec0(embedding float[4])")

with db:
    for item in items:
        db.execute(
            "INSERT INTO vec_items(rowid, embedding) VALUES (?, ?)",
            [item[0], serialize_f32(item[1])],
        )

rows = db.execute(
    """
    SELECT
        rowid,
        distance
    FROM vec_items
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 3
    """,
    [serialize_f32(query)],
).fetchall()

print(rows)


if __name__ == "__main__":
    check_sqlite_vec()
