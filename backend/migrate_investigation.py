from sqlalchemy import inspect, text

from database.database import engine


def add_investigation_column():

    inspector = inspect(engine)

    columns = [
        column["name"]
        for column in inspector.get_columns("tickets")
    ]

    if "investigation_data" in columns:

        print(
            "investigation_data column already exists."
        )

        return

    with engine.begin() as connection:

        connection.execute(
            text(
                "ALTER TABLE tickets "
                "ADD COLUMN investigation_data TEXT"
            )
        )

    print(
        "investigation_data column added successfully."
    )


if __name__ == "__main__":

    add_investigation_column()