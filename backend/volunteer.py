import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin123",
        database="login1"
    )


def fetch_filtered_volunteers(skill, location):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # SQL query jo sirf matching skills aur location dhundegi
    # % symbols ka matlab hai "agar ye word kahin bhi match kare"
    query = "SELECT * FROM volunteer WHERE skills LIKE %s AND location LIKE %s"
    cursor.execute(query, (f"%{skill}%", f"%{location}%"))
    
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return data