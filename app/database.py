import pymysql
from config import Config


def get_connection():
    """Open a new MySQL connection using settings from Config.

    Returns a pymysql connection with a DictCursor, so query results
    come back as dictionaries (e.g. row["email"]) instead of tuples.
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )