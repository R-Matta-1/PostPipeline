import sqlite3
import os

DB_PATH = "storage/pending.db"

def get_connection():
    # Ensure the storage directory exists
    os.makedirs("storage", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            platform TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_draft(title, content, platform):
    """CREATE: Adds a new draft to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    full_content = f"{title}\n{content}"
    cursor.execute('INSERT INTO drafts (content, platform) VALUES (?, ?)', (full_content, platform))
    conn.commit()
    draft_id = cursor.lastrowid
    conn.close()
    return draft_id

def get_all_pending():
    """READ: Returns a list of all PENDING drafts."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts WHERE status = 'PENDING'")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_pending_count():
    """READ: Returns the count of PENDING drafts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM drafts WHERE status = 'PENDING'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_draft_by_id(draft_id):
    """READ: Returns a single draft by ID."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_status(draft_id, new_status):
    """UPDATE: Changes status (e.g., 'PUBLISHED')."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE drafts SET status = ? WHERE id = ?', (new_status, draft_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def delete_draft(draft_id):
    """DELETE: Removes a draft record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drafts WHERE id = ?', (draft_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success