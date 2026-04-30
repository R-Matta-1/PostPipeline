import asyncio
import sys
import json
import os
from core.UiMethods import  TerminalTexter #,TelegramBot, WhatsAppBot
from core.database import init_db, get_pending_count

CONFIG_PATH = "config/Social.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def configure_system():
    """Manual configuration CLI for first-time setup or --configure flag."""
    print("--- System Configuration ---")
    method = input("Choose communication method (telegram/whatsapp/terminal): ").strip().lower()
    target = input("Enter default social media target (e.g., Facebook, LinkedIn, X): ").strip()
    token = input("Enter API Token: ")
    
    config = {
        "method": method,
        "target_platform": target,
        "api_token": token,
        "poll_interval": 15
    }
    
    os.makedirs("config", exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"Configuration saved to {CONFIG_PATH}\n")
    return config

async def poll_loop(bot, interval):
    """The always-listening loop that branches into CRUD tasks."""
    print(f"Listener active. Polling every {interval}s...")
    
    while True:
        # 1. Poll for updates (This logic depends on the specific API)
        updates = await bot.get_updates() 
        
        for update in updates:
            # The 'Switch' (Match) statement for command routing
            # Lowercase everything for case-insensitive comparison
            command = update.get("text", "").split()
            cmd_lower = command[0].lower() if command else ""
            args = command[1:] if len(command) > 1 else []

            match cmd_lower:
                case "/generate":
                    asyncio.create_task(bot.handle_generate(args))
                case "/list":
                    await bot.handle_list()
                case "/view":
                    await bot.handle_view(args[0] if args else None)
                case "/accept":
                    await bot.handle_accept(args[0] if args else None)
                case "/cancel":
                    await bot.handle_cancel(args[0] if args else None)
                case "/dumbpost":
                    asyncio.create_task(bot.handle_dumbpost(args[0] if args else None))
                case _:
                    print(f"Unknown command received: {command}")

        await asyncio.sleep(interval)

async def main():
    # Ensure database is initialized
    init_db()
    
    # Check for config file or --configure flag
    force_config = "--configure" in sys.argv
    config = load_config()

    if not config or force_config:
        config = configure_system()

    # Polymorphic instantiation based on config
    method = config["method"].lower()
    match method:
#        case "telegram":
#            bot = TelegramBot(config["api_token"])
#        case "whatsapp":
#            bot = WhatsAppBot(config["api_token"])
        case "terminal":
            bot = TerminalTexter()
        case _:
            print("Invalid method in config.")
            return

    # Start the non-blocking polling loop
    try:
        await poll_loop(bot, config.get("poll_interval", 1))
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

if __name__ == "__main__":
    asyncio.run(main())