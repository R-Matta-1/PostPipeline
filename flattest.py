#!/usr/bin/env python3
"""Flattened single-file version of PostPipeline. Operates identically to main.py but with no external dependencies."""
import asyncio
import sqlite3
import os
import json
import sys
import random

# === CONFIG ===
CONFIG_PATH = "config/Social.json"
DB_PATH = "storage/pending.db"

# === DATABASE ===
def get_conn():
    os.makedirs("storage", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.execute('''
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
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO drafts (content, platform) VALUES (?, ?)', (f"{title}\n{content}", platform))
    conn.commit()
    draft_id = cursor.lastrowid
    conn.close()
    return draft_id

def get_all_pending():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts WHERE status = 'PENDING'")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_draft_by_id(draft_id):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_status(draft_id, new_status):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('UPDATE drafts SET status = ? WHERE id = ?', (new_status, draft_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def delete_draft(draft_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drafts WHERE id = ?', (draft_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

# === GENERATOR ===
async def generate_dummy_post():
    topics = ["AI", "Machine Learning", "Python", "AsyncIO", "Social Media", "Content Creation", "Automation"]
    actions = ["exploring", "building", "optimizing", "innovating with", "leveraging", "mastering"]
    outcomes = ["new possibilities", "efficiency gains", "smarter workflows", "cutting-edge solutions", "enhanced engagement"]
    topic, action, outcome = random.choice(topics), random.choice(actions), random.choice(outcomes)
    await asyncio.sleep(1)
    return {"title": f"Dummy Post about {topic}", "content": f"Just {action} {topic} to unlock {outcome}! #AI #Tech #Innovation", "platform": "terminal"}

# === POSTER ===
async def post_to_platform(platform, title, content):
    print(f"\n--- SIMULATED POST TO {platform.upper()} ---")
    print(f"Title: {title}\nContent: {content}\n----------------------------------\n")
    return True

# === CONFIG ===
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def configure_system():
    print("--- System Configuration ---")
    method = input("Choose communication method (telegram/whatsapp/terminal): ").strip().lower()
    target = input("Enter default social media target (e.g., Facebook, LinkedIn, X): ").strip()
    token = input("Enter API Token: ")
    config = {"method": method, "target_platform": target, "api_token": token, "poll_interval": 15}
    os.makedirs("config", exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration saved to {CONFIG_PATH}\n")
    return config

# === HANDLERS ===
async def handle_generate():
    print("Generating a post...")
    post = await generate_dummy_post()
    print(f"Generated Post:\n\nTitle: {post['title']}\nContent: {post['content']}\nPlatform: {post['platform']}\n")
    resp = input("Accept and post? (yes/no): ").lower().strip()
    if resp == 'yes':
        draft_id = save_draft(post["title"], post["content"], post["platform"])
        print(f"Draft #{draft_id} saved as PENDING. Publishing...")
        await handle_accept(str(draft_id))
    else:
        print("Post discarded.")

async def handle_list():
    drafts = get_all_pending()
    if not drafts:
        print("No pending drafts found.")
        return
    print("--- Pending Drafts ---")
    for d in drafts:
        print(f"ID: {d['id']} | Platform: {d['platform']} | Created: {d['created_at']}")

async def handle_view(draft_id):
    if not draft_id:
        print("Error: Please provide a draft ID (e.g., /view 1)")
        return
    draft = get_draft_by_id(draft_id)
    if draft:
        print(f"Viewing Draft #{draft_id}:\n\n{draft['content']}")
    else:
        print(f"No draft found with ID: {draft_id}")

async def handle_accept(draft_id):
    if not draft_id:
        print("Error: Please provide a draft ID (e.g., /accept 1)")
        return
    draft = get_draft_by_id(draft_id)
    if not draft:
        print(f"No draft found with ID: {draft_id}")
        return
    title, content = draft['content'].split('\n', 1)
    if await post_to_platform(draft['platform'], title, content):
        if update_status(draft_id, "PUBLISHED"):
            print(f"Draft #{draft_id} has been PUBLISHED to {draft['platform']}.")
        else:
            print("Failed to update draft status to PUBLISHED.")
    else:
        print(f"Failed to publish draft #{draft_id} to {draft['platform']}.")

async def handle_cancel(draft_id):
    if delete_draft(draft_id):
        print(f"Draft #{draft_id} deleted successfully.")
    else:
        print(f"Failed to delete draft #{draft_id}.")

async def handle_dumbpost(draft_id):
    if not draft_id:
        print("Error: Please provide a draft ID (e.g., /dumbpost 1)")
        return
    draft = get_draft_by_id(draft_id)
    if not draft:
        print(f"No draft found with ID: {draft_id}")
        return
    title, content = draft['content'].split('\n', 1)
    print(f"Simulating 'dumb post' for Draft #{draft_id} to {draft['platform']}...")
    if await post_to_platform(draft['platform'], title, content):
        if delete_draft(draft_id):
            print(f"Draft #{draft_id} 'dumb posted' and deleted successfully.")
        else:
            print(f"Draft #{draft_id} 'dumb posted' but failed to delete.")
    else:
        print(f"Failed to 'dumb post' draft #{draft_id} to {draft['platform']}.")

# === POLL LOOP ===
async def poll_loop(interval):
    print(f"Listener active. Polling every {interval}s...")
    while True:
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, "bot > ")
        if not user_input:
            continue
        command = user_input.strip().split()
        cmd_lower = command[0].lower() if command else ""
        args = command[1:] if len(command) > 1 else []

        match cmd_lower:
            case "/generate":
                asyncio.create_task(handle_generate())
            case "/list":
                await handle_list()
            case "/view":
                await handle_view(args[0] if args else None)
            case "/accept":
                await handle_accept(args[0] if args else None)
            case "/cancel":
                await handle_cancel(args[0] if args else None)
            case "/dumbpost":
                asyncio.create_task(handle_dumbpost(args[0] if args else None))
            case _:
                print(f"Unknown command received: {cmd_lower}")
        await asyncio.sleep(interval)

# === MAIN ===
async def main():
    init_db()
    force_config = "--configure" in sys.argv
    config = load_config()
    if not config or force_config:
        config = configure_system()
    try:
        await poll_loop(config.get("poll_interval", 1))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

if __name__ == "__main__":
    asyncio.run(main())