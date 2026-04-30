class Poster:
    async def post_to_platform(self, platform: str, title: str, content: str):
        if platform == "terminal":
            print(f"\n--- SIMULATED POST TO TERMINAL ---")
            print(f"Platform: {platform}")
            print(f"Title: {title}")
            print(f"Content: {content}")
            print(f"----------------------------------\n")
            return True
        # Add other platforms here later
        else:
            print(f"Error: Unknown platform '{platform}' for posting.")
            return False
