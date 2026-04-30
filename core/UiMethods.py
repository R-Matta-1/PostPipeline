import asyncio
from core.database import get_all_pending, get_draft_by_id, update_status, delete_draft
from abc import ABC, abstractmethod
from core.dummy_generator import generate_dummy_post
from core.poster import Poster

class Texter(ABC):
    """The Superclass (Interface) ensuring all bots speak the same language."""
    @abstractmethod
    async def get_updates(self):
        pass

    @abstractmethod
    async def send_message(self, content: str):
        pass

class TerminalTexter(Texter):
    def __init__(self):
        print("\n[System] Terminal Mode Active. Type commands directly below.")
        self.poster = Poster()

    async def get_updates(self):
        """Simulates polling by asking for user input via terminal."""
        # We use run_in_executor because standard input() is blocking
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, "bot > ")
        
        if not user_input:
            return []

        # Wrap in a list to mimic the structure of API updates
        return [{"text": user_input}]

    async def send_message(self, content: str):
        print(f"\n[OUTGOING]:\n{content}\n")

    # --- CRUD Handlers ---

    async def handle_generate(self, args):
        await self.send_message(f"Generating a dummy post...")
        
        # Generate dummy post
        post_data = await generate_dummy_post()
        
        # Display the generated post to the user
        await self.send_message(f"Generated Post:\n\nTitle: {post_data['title']}\nContent: {post_data['content']}\nPlatform: {post_data['platform']}\n")

        # Ask for user confirmation
        user_response = (await asyncio.to_thread(input, "Do you want to accept and post this draft? (yes/no): ")).lower()

        if user_response == 'yes':
            # Save to DB
            from core.database import save_draft # Import here to avoid circular dependency if database imports UiMethods
            draft_id = save_draft(post_data["title"], post_data["content"], post_data["platform"])
            await self.send_message(f"Draft #{draft_id} saved as PENDING. Attempting to publish...")
            await self.handle_accept(str(draft_id)) # Call handle_accept to publish
        else:
            await self.send_message("Post discarded.")

    async def handle_list(self):
        drafts = get_all_pending()
        if not drafts:
            await self.send_message("No pending drafts found.")
            return
        
        summary = "--- Pending Drafts ---\n"
        for d in drafts:
            summary += f"ID: {d['id']} | Platform: {d['platform']} | Created: {d['created_at']}\n"
        await self.send_message(summary)

    async def handle_view(self, draft_id):
        if not draft_id:
            await self.send_message("Error: Please provide a draft ID (e.g., /view 1)")
            return
            
        draft = get_draft_by_id(draft_id)
        if draft:
            await self.send_message(f"Viewing Draft #{draft_id}:\n\n{draft['content']}")
        else:
            await self.send_message(f"No draft found with ID: {draft_id}")

    async def handle_accept(self, draft_id):
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
        if delete_draft(draft_id):
            await self.send_message(f"Draft #{draft_id} deleted successfully.")
        else:
            await self.send_message(f"Failed to delete draft #{draft_id}.")

    async def handle_dumbpost(self, draft_id):
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