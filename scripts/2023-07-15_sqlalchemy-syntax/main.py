from sqlalchemy import Column, Integer, MetaData, Table, create_engine, insert, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# create engine

engine = create_engine("sqlite+pysqlite:///database.db", echo=True, future=True)
session_factory = sessionmaker(bind=engine, future=True)
session = session_factory()


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# create metadata

base_metadata = MetaData()
Base = declarative_base(metadata=base_metadata)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# create table

stmt = text(
    """
        CREATE TABLE foobar (x int, y int)
    """
)

with engine.connect() as conn:
    conn.execute(stmt)
    conn.commit()


# drop table

stmt = text(
    """
        DROP TABLE foobar
    """
)

with engine.connect() as conn:
    conn.execute(stmt)
    conn.commit()


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# define table

foobar = Table(
    "foobar",
    base_metadata,
    Column("x", Integer, nullable=False),
    Column("y", Integer, nullable=False),
)


# create table

foobar.create(engine, checkfirst=True)


# drop table

foobar.drop(engine, checkfirst=True)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# define table


class FooBar(Base):
    __tablename__ = "foobar"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)


# create table

FooBar.__table__.create(engine, checkfirst=True)


# drop table

FooBar.__table__.drop(engine, checkfirst=True)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# insert records into table (textual SQL)


## single record - pass parameters to accompany SQL statement

stmt = text(
    """
        INSERT INTO foobar (x, y) VALUES (:x, :y)
    """
)
record = {"x": 1, "y": 2}

with engine.connect() as conn:
    conn.execute(stmt, record)
    conn.commit()


## multiple records - pass parameters to accompany SQL statement

stmt = text(
    """
        INSERT INTO foobar (x, y) VALUES (:x, :y)
    """
)
record = [{"x": 3, "y": 4}, {"x": 5, "y": 6}]

with engine.connect() as conn:
    conn.execute(stmt, record)
    conn.commit()


## single record - bundle parameters to SQL statement

stmt = text(
    """
        INSERT INTO foobar (x, y) VALUES (:x, :y)
    """
)
stmt = stmt.bindparams(x=10, y=11)

with engine.connect() as conn:
    conn.execute(stmt)
    conn.commit()


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# insert records into table (Core)

## single record - implicitly / automatically create VALUES clause from Connection.execute() method

stmt = insert(foobar)
record = {"x": 1, "y": 2}

with engine.connect() as conn:
    conn.execute(stmt, record)
    conn.commit()


## multiple records - implicitly / automatically create VALUES clause from Connection.execute() method

stmt = insert(foobar)
record = [{"x": 3, "y": 4}, {"x": 5, "y": 6}]

with engine.connect() as conn:
    conn.execute(stmt, record)
    conn.commit()


## single record - explicitly create VALUES clause

stmt = insert(foobar).values(x=333, y=777)

with engine.connect() as conn:
    conn.execute(stmt)
    conn.commit()


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---


# insert records into table (ORM)


record = FooBar(x=1, y=2)
session.add(record)
session.commit()
