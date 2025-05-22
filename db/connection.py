import aiomysql
import os

from dotenv import load_dotenv

load_dotenv()

MYSQL_CONNECTION_DATA = {
    "host": os.environ.get("MYSQL_HOST"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "db": os.environ.get("MYSQL_DB"),
}


async def get_mysql_connection() -> aiomysql.Connection:
    return await aiomysql.connect(**MYSQL_CONNECTION_DATA)


async def create_tables():
    connection = await get_mysql_connection()
    try:
        cursor = await connection.cursor()
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT,
                user_id INT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                token TEXT,
                low_limit INTEGER,
                high_limit INTEGER,
                notices BOOLEAN NOT NULL,
                PRIMARY KEY(id)
            );
            """
        )
        await connection.commit()
    except aiomysql.Error as e:
        raise e
    finally:
        connection.close()