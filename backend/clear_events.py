from app.db.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DELETE FROM events;")

conn.commit()
conn.close()

print("✅ All events cleared.")