import asyncio
from core.database import get_all_pending, get_draft_by_id, update_status, delete_draft
from abc import ABC, abstractmethod
from core.dummy_generator import generate_dummy_post
from core.poster import Poster


class Texter(ABC):
    """Abstract base class for all messaging platforms."""
    
    def __init__(self):
        self.poster = Poster()
    
    @abstractmethod
    async def get_updates(self):
        """Poll for new messages/commands from the platform."""
        pass

    @abstractmethod
    async def send_message(self, content: str):
        """Send a message to the user or channel."""
        pass

    @abstractmethod
    async def close(self):
        """Clean up resources (close connections, etc.)."""
        pass

    # --- Template Methods (CRUD operations) ---
    # These provide default implementations but can be overridden
    
    async def handle_generate(self):
        """Generate a dummy post and optionally save it."""
        await self.send_message("Generating a dummy post...")
        post_data = await generate_dummy_post(platform=self.platform)
        await self.send_message(
            f"Generated Post:\n\nTitle: {post_data['title']}\n"
            f"Content: {post_data['content']}\nPlatform: {post_data['platform']}"
        )
        
        user_response = (await asyncio.to_thread(input, "Accept and post? (yes/no): ")).lower()
        if user_response == 'yes':
            from core.database import save_draft
            draft_id = save_draft(post_data["title"], post_data["content"], post_data["platform"])
            await self.send_message(f"Draft #{draft_id} saved as PENDING. Publishing...")
            await self.handle_accept(str(draft_id))
        else:
            await self.send_message("Post discarded.")

    async def handle_list(self):
        """List all pending drafts."""
        drafts = get_all_pending()
        if not drafts:
            await self.send_message("No pending drafts found.")
            return
        
        summary = "--- Pending Drafts ---\n"
        for d in drafts:
            summary += f"ID: {d['id']} | Platform: {d['platform']} | Created: {d['created_at']}\n"
        await self.send_message(summary)

    async def handle_view(self, draft_id):
        """View a specific draft by ID."""
        if not draft_id:
            await self.send_message("Error: Please provide a draft ID (e.g., /view 1)")
            return
            
        draft = get_draft_by_id(draft_id)
        if draft:
            await self.send_message(f"Viewing Draft #{draft_id}:\n\n{draft['content']}")
        else:
            await self.send_message(f"No draft found with ID: {draft_id}")

    async def handle_accept(self, draft_id):
        """Publish a draft and mark it as PUBLISHED."""
        if not draft_id:
            await self.send_message("Error: Please provide a draft ID (e.g., /accept 1)")
            return
        
        draft = get_draft_by_id(draft_id)
        if not draft:
            await self.send_message(f"No draft found with ID: {draft_id}")
            return

        title, content = draft['content'].split('\n', 1)

        if await self.poster.post_to_platform(draft['platform'], title, content):
            if update_status(draft_id, "PUBLISHED"):
                await self.send_message(f"Draft #{draft_id} has been PUBLISHED to {draft['platform']}.")
            else:
                await self.send_message("Failed to update draft status to PUBLISHED.")
        else:
            await self.send_message(f"Failed to publish draft #{draft_id} to {draft['platform']}.")

    async def handle_cancel(self, draft_id):
        """Delete a draft."""
        if delete_draft(draft_id):
            await self.send_message(f"Draft #{draft_id} deleted successfully.")
        else:
            await self.send_message(f"Failed to delete draft #{draft_id}.")

    async def handle_dumbpost(self, draft_id):
        """Publish and delete a draft in one step."""
        if not draft_id:
            await self.send_message("Error: Please provide a draft ID (e.g., /dumbpost 1)")
            return
        
        draft = get_draft_by_id(draft_id)
        if not draft:
            await self.send_message(f"No draft found with ID: {draft_id}")
            return

        title, content = draft['content'].split('\n', 1)

        await self.send_message(f"Simulating 'dumb post' for Draft #{draft_id} to {draft['platform']}...")
        if await self.poster.post_to_platform(draft['platform'], title, content):
            if delete_draft(draft_id):
                await self.send_message(f"Draft #{draft_id} 'dumb posted' and deleted successfully.")
            else:
                await self.send_message(f"Draft #{draft_id} 'dumb posted' but failed to delete.")
        else:
            await self.send_message(f"Failed to 'dumb post' draft #{draft_id} to {draft['platform']}.")

    # --- Command Router ---
    
    async def process_command(self, raw_input: str):
        """Parse and route commands to handlers. Case-insensitive."""
        parts = raw_input.strip().split(maxsplit=1)
        command = parts[0].lower() if parts else ""  # Force lowercase
        args = parts[1] if len(parts) > 1 else None

        handlers = {
            "/generate": self.handle_generate,
            "/list": self.handle_list,
            "/view": lambda _: self.handle_view(args),
            "/accept": lambda _: self.handle_accept(args),
            "/cancel": lambda _: self.handle_cancel(args),
            "/dumbpost": lambda _: self.handle_dumbpost(args),
            "/help": self._handle_help,
        }

        handler = handlers.get(command)
        if handler:
            await handler(args)
        else:
            await self.send_message(f"Unknown command: {command}. Type /help for available commands.")

    async def _handle_help(self, _=None):
        """Show available commands."""
        await self.send_message(
            "Available commands:\n"
            "/generate - Create a dummy post\n"
            "/list - Show pending drafts\n"
            "/view <id> - View a draft\n"
            "/accept <id> - Publish a draft\n"
            "/cancel <id> - Delete a draft\n"
            "/dumbpost <id> - Publish and delete\n"
            "/help - Show this help"
        )


class TerminalTexter(Texter):
    """Terminal-based implementation using stdin/stdout."""
    
    def __init__(self):
        super().__init__()
        print("\n[System] Terminal Mode Active. Type commands directly below.")

    async def get_updates(self):
        """Poll for user input via terminal."""
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, "bot > ")
        return [{"text": user_input}] if user_input else []

    async def send_message(self, content: str):
        print(f"\n[OUTGOING]:\n{content}\n")

    async def close(self):
        print("\n[System] Terminal session closed.")


# --- Factory for creating Texter instances ---

class TexterFactory:
    """Factory to create the appropriate Texter based on configuration."""
    
    _implementations = {
        "terminal": TerminalTexter,
        # Future implementations:
        # "telegram": TelegramTexter,
        # "discord": DiscordTexter,
    }
    
    @classmethod
    def create(cls, platform: str = "terminal", **kwargs) -> Texter:
        """Create a Texter instance for the specified platform."""
        texter_class = cls._implementations.get(platform.lower())
        if not texter_class:
            raise ValueError(f"Unknown platform: {platform}. Available: {list(cls._implementations.keys())}")
        return texter_class(**kwargs)
    
    @classmethod
    def register(cls, name: str, texter_class: type):
        """Register a new Texter implementation."""
        cls._implementations[name.lower()] = texter_class