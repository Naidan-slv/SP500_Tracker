from sqlalchemy import text

from app.database.connection import engine


def main() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar_one()
        if value == 1:
            print("✅ Database connection successful.")
        else:
            raise RuntimeError("Unexpected DB response.")


if __name__ == "__main__":
    main()
