import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    port=3308,
    user="wedplan_app",
    password="YOUR_MYSQL_PASSWORD",
    database="wedplan_smart"
)

if connection.is_connected():
    print("Connected successfully!")