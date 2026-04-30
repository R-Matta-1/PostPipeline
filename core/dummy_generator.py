import random
import asyncio

async def generate_dummy_post():
    """Generates a random dummy social media post for testing."""
    topics = ["AI", "Machine Learning", "Python", "AsyncIO", "Social Media", "Content Creation", "Automation"]
    actions = ["exploring", "building", "optimizing", "innovating with", "leveraging", "mastering"]
    outcomes = ["new possibilities", "efficiency gains", "smarter workflows", "cutting-edge solutions", "enhanced engagement"]

    topic = random.choice(topics)
    action = random.choice(actions)
    outcome = random.choice(outcomes)

    post_content = f"Just {action} {topic} to unlock {outcome}! #AI #Tech #Innovation"
    
    # Simulate async operation
    await asyncio.sleep(1) 
    
    return {
        "title": f"Dummy Post about {topic}",
        "content": post_content,
        "platform": "terminal", # Default for dummy
        "status": "PENDING"
    }
