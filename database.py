import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3308,
        user="wedplan_app",
        password="Afrin@123",
        database="wedplan_smart"
    )

