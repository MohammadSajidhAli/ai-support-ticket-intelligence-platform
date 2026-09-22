import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./tickets.db"
)


connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def add_resolution_columns():

    columns = [
        (
            "approval_status",
            "VARCHAR(50)"
        ),
        (
            "approved_by",
            "VARCHAR(255)"
        ),
        (
            "approval_comment",
            "TEXT"
        ),
        (
            "resolution_action",
            "TEXT"
        ),
        (
            "resolution_status",
            "VARCHAR(50)"
        ),
        (
            "resolution_message",
            "TEXT"
        )
    ]

    with engine.connect() as connection:

        existing_columns = connection.execute(
            text("PRAGMA table_info(tickets)")
        ).fetchall()

        existing_column_names = {
            column[1]
            for column in existing_columns
        }

        for column_name, column_type in columns:

            if column_name not in existing_column_names:

                connection.execute(
                    text(
                        f"""
                        ALTER TABLE tickets
                        ADD COLUMN {column_name}
                        {column_type}
                        """
                    )
                )

        connection.commit()