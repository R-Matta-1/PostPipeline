# AsyncAI-Social-Orchestrator

## Overview
A robust, asynchronous Content Management System (CMS) designed for automated social media content generation. The system leverages **CrewAI** for autonomous research and drafting, while maintaining a **Human-in-the-Loop (HITL)** verification process through a chat-based interface.

### Key Technical Pillars
* **Polymorphic Egress:** Implements a `Texter` abstract base class to decouple social platform APIs (Telegram, WhatsApp, Terminal) from business logic.
* **Asynchronous Processing:** Utilizes `asyncio` to maintain a non-blocking event loop, ensuring the listener remains responsive during intensive AI research tasks.
* **Persistence & Integrity:** Employs a **SQLite** relational storage layer to manage content lifecycle (CRUD), ensuring state recovery and data consistency.



## CRUD Workflow
The bot manages content objects through a lifecycle-based command interface. All states are persisted in `storage/pending.db`. 

| Command | Operation | Description |
| :--- | :--- | :--- |
| `/generate` | **Create** | Triggers an async `CrewAI` task; commits draft to DB as `PENDING`. |
| `/list` | **Read** | Queries the DB for all current `PENDING` drafts. |
| `/view <id>` | **Read** | Retrieves specific content and metadata for review. |
| `/modify <id>` | **Update** | Updates DB record; supports iterative refinement. |
| `/cancel <id>` | **Delete** | Removes record from persistence layer. |
| `/accept <id>` | **Execute** | Finalizes draft and publishes via the Polymorphic Egress layer. |

## Workflow Sequence


## Project Structure
```text
.
├── main.py              # Entry point: Async event loop and bot initialization
├── config/
│   └── Social.json      # Sensitive credentials and environment variables
├── core/
│   ├── database.py      # CRUD interface for SQLite operations
│   ├── crew_logic.py    # Multi-agent research and composition workflows
│   └── polymorphism.py  # Abstract Texter interface and concrete implementations
└── storage/
    └── pending.db       # SQLite local persistence
```

## Engineering Highlights
* **Stateful Reliability:** By treating drafts as database records, the system is resilient to process crashes. Unfinished work remains safely stored in the `pending.db`.
* **Dependency Injection:** Configuration is managed solely in the entry point and injected into class constructors, facilitating unit testing and environment-specific deployments.
* **Non-Blocking Execution:** Spawning AI agents as `asyncio` tasks allows the system to process multiple user interactions concurrently without command timeouts.

## Setup & Configuration
1.  **Environment:** Ensure `Python 3.10+` is installed.
2.  **Dependencies:** `pip install -r requirements.txt` (includes `sqlite3`, `asyncio`, `crewai`).
3.  **Config:** Populate `config/Social.json` with required API tokens and platform parameters.
4.  **Init:** Run `python main.py` to initialize the SQLite schema and start the listener loop.
