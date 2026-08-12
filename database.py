import mysql.connector


def get_db_connection():

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="online_shopping"
    )

    return connection