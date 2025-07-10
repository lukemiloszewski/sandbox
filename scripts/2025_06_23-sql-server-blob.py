from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, LargeBinary
from sqlalchemy.engine import make_url

datastore_url = make_url(...)
engine = create_engine(datastore_url)

base_metadata = MetaData()

test_attachments = Table(
    "test_attachments",
    base_metadata,
    Column("id", Integer, autoincrement=True, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("attachment", LargeBinary, nullable=True),
    schema="dbo",
)


def create_test_table():
    base_metadata.create_all(engine, tables=[test_attachments])


def cleanup_test_table():
    base_metadata.drop_all(engine, tables=[test_attachments])


def insert_attachment(pdf_file_path, attachment_name):
    with open(pdf_file_path, "rb") as file:
        pdf_data = file.read()

    sql = """
    INSERT INTO dbo.test_attachments (name, attachment)
    VALUES (:name, :attachment)
    """
    stmt = text(sql)

    with engine.begin() as conn:
        conn.execute(stmt, {"name": attachment_name, "attachment": pdf_data})


def retrieve_attachment(attachment_id, output_path):
    sql = """
    SELECT name, attachment 
    FROM dbo.test_attachments 
    WHERE id = :id
    """
    stmt = text(sql)

    with engine.connect() as conn:
        result = conn.execute(stmt, {"id": attachment_id})
        row = result.fetchone()

        if row:
            _, attachment_data = row
            with open(output_path, "wb") as file:
                file.write(attachment_data)


def list_attachments():
    sql = """
    SELECT id, name 
    FROM dbo.test_attachments 
    ORDER BY id
    """
    stmt = text(sql)

    with engine.connect() as conn:
        result = conn.execute(stmt)
        return result.all()


if __name__ == "__main__":
    create_test_table()

    insert_attachment("data/bitcoin.pdf", "Bitcoin Whitepaper")

    attachments = list_attachments()
    print("Attachments in the database:")
    for attachment in attachments:
        print(f"ID: {attachment.id}, Name: {attachment.name}")

    retrieve_attachment(1, "data/output.pdf")

    cleanup_test_table()
