# ADK Telegram (`adkt`)

[![PyPI version](https://badge.fury.io/py/adkt.svg)](https://badge.fury.io/py/adkt) <!-- Assuming 'adkt' is the name on PyPI -->
<!-- Add other badges like license, build status if applicable -->

A Python library that simplifies the integration of Google's Agent Development Kit (ADK) with Telegram bots. It provides a high-level wrapper using `python-telegram-bot` to quickly deploy ADK-powered agents that can interact via Telegram, including proactively sending messages back to the user.

## Key Features

*   **Simplified Boilerplate:** Reduces the setup code needed to connect an ADK agent to a Telegram interface.
*   **Session Management:** Automatically handles ADK sessions per unique Telegram chat ID using `InMemorySessionService`.
*   **Runner Management:** Manages ADK `Runner` instances for each active chat.
*   **Agent-Initiated Messages:** Includes a mechanism to provide a specific tool (`send_telegram_message_tool`) to your ADK agent, allowing it to send messages back to the Telegram chat proactively during its execution flow.
*   **Built on `python-telegram-bot`:** Leverages the popular and robust `python-telegram-bot` library (v21+ recommended).
*   **Configurable:** Supports restricting bot access to specific chat IDs and enabling debug logging.

## Installation

Install `adkt`:

```bash
pip install adkt
```

## Core Concept: Agent Sending Messages

A key feature of `adkt` is enabling the ADK agent itself to send messages back to the user. This is achieved by:

1.  The `TelegramBot` wrapper dynamically creates a function (`send_telegram_message_tool` internally) for each chat that knows how to send a message to that specific chat ID via the Telegram Bot API.
2.  This function is passed as an argument to your `generate_agent_fn` when a new agent/runner is created for a chat.
3.  Your `generate_agent_fn` must accept this tool (e.g., as `send_telegram_message_tool`) and include it in the `tools` list when creating the `LlmAgent`.
4.  You must instruct your LLM (via the agent's `instruction` prompt) to use this specific tool whenever it needs to communicate back to the user.

## Basic Usage

Here's a typical structure for using `adkt`:

**1. Set up your Environment (`.env` file):**

```dotenv
TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
# Optional: Restrict to specific chat IDs (comma-separated)
# TELEGRAM_CHAT_IDS="12345678,98765432"
```

*   Get your `TELEGRAM_TOKEN` from [BotFather](https://core.telegram.org/bots#botfather) on Telegram.

**2. Create your main Python script (e.g., `main.py`):**

```python
import os
from dotenv import load_dotenv

from adkt import start_agent_bot # Import the main function from adkt
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm # Example using LiteLLM

# Load environment variables from .env file
load_dotenv()

# --- Define Your Agent's Tools ---
def lookup_order_status(order_id: str) -> dict:
  """Fetches the current status of a customer's order using its ID.

  Use this tool ONLY when a user explicitly asks for the status of
  a specific order and provides the order ID. Do not use it for
  general inquiries.

  Args:
      order_id: The unique identifier of the order to look up.

  Returns:
      A dictionary containing the order status.
      Possible statuses: 'shipped', 'processing', 'pending', 'error'.
      Example success: {'status': 'shipped', 'tracking_number': '1Z9...'}
      Example error: {'status': 'error', 'error_message': 'Order ID not found.'}
  """
  print(f"Tool: Looking up status for order_id: {order_id}")
  # Replace with your actual order lookup logic
  if order_id == "123":
      return {"status": 'processing', "tracking_number": '1ZABCDEF987'}
  else:
      return {"status": 'error', 'error_message': f'Order ID {order_id} not found.'}

# --- Define Your Agent Generation Function ---
# This function MUST accept 'user_id' and the messaging tool ('send_telegram_message_tool')
def generate_agent(user_id: str, send_telegram_message_tool: callable) -> LlmAgent:
    """
    Creates and configures the ADK Agent instance for a specific user.

    Args:
        user_id: The unique identifier for the user (derived from chat_id).
        send_telegram_message_tool: The tool function provided by adkt
                                     for sending messages back to this user's chat.
    Returns:
        An configured LlmAgent instance.
    """
    print(f"Generating agent for user_id: {user_id}")

    # Configure your LLM connection (Example uses LiteLLM for Ollama)
    # Ensure your Ollama server is running and has the model pulled.
    llm_model = LiteLlm(model="ollama/yasserrmd/Llama-4-Scout-17B-16E-Instruct", api_base="http://localhost:11434") # Adjust api_base if needed

    agent_instruction = """You are a helpful assistant interacting via Telegram.
Your goal is to answer user questions and fulfill requests.
You have access to the following tools:
1. `lookup_order_status`: Use this ONLY when the user asks for the status of a specific order and provides the ID.
2. `send_telegram_message`: This is the **ONLY** way to communicate back to the user. Use this tool for *all* responses, including asking for clarification, providing updates, confirming actions, and delivering the final answer. Do not output plain text, always use this tool.
"""

    agent = LlmAgent(
        model=llm_model,
        name=f"telegram_agent_{user_id}", # Unique name per user is good practice
        instruction=agent_instruction,
        tools=[
            lookup_order_status,
            send_telegram_message_tool # IMPORTANT: Include the provided messaging tool
            ]
    )
    return agent

# --- Start the Bot ---
if __name__ == "__main__":
    print("Starting ADK Telegram Bot...")
    telegram_token = os.environ.get("TELEGRAM_TOKEN")
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN not found in environment variables.")

    # Optional: Load restricted chat IDs if set
    restricted_chats_str = os.environ.get("TELEGRAM_CHAT_IDS")
    restricted_chat_ids = restricted_chats_str.split(',') if restricted_chats_str else None

    start_agent_bot(
        telegram_token=telegram_token,
        generate_agent_fn=generate_agent, # Pass your agent generator function
        telegram_chat_ids=restricted_chat_ids, # Pass list of allowed chat IDs, or None
        debug=True # Enable verbose logging from adkt and ADK
    )
```

**3. Run the script:**

```bash
python main.py
```

**4. Interact with your Bot:**
Find your bot on Telegram and start sending messages. The agent defined in `generate_agent` will process them, potentially using the `lookup_order_status` tool and sending responses back via the `send_telegram_message_tool`. Use the `/get_chat_id` command if you need to find your chat ID for the `TELEGRAM_CHAT_IDS` setting.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.
