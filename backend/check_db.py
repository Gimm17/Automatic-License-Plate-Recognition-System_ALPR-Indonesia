import sqlite3
import sys
sys.path.insert(0, '.')

db_path = r'storage/alpr_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check cameras table DDL
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='cameras'")
row = cursor.fetchone()
print('CAMERAS TABLE DDL:')
print(row[0] if row else 'TABLE NOT FOUND')

# Try raw insert
try:
    cursor.execute("INSERT INTO cameras (name, rtsp_url, is_active, stream_fps, created_at) VALUES ('RawTest', 'rtsp://test', 1, 5, datetime('now'))")
    conn.commit()
    cursor.execute("SELECT id, name FROM cameras WHERE name='RawTest'")
    print('RAW INSERT OK:', cursor.fetchone())
    cursor.execute("DELETE FROM cameras WHERE name='RawTest'")
    conn.commit()
except Exception as e:
    print('RAW INSERT ERROR:', e)

conn.close()
