import sqlite3

conn = sqlite3.connect("fashion_metadata.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS saved_outfits")
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS search_history")

conn.commit()
conn.close()
