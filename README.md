# Smol Agents Telegram Bot Wrapper (SmolAgentsTelegram)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/SmolAgentsTelegram.svg)](https://badge.fury.io/py/SmolAgentsTelegram)

A Python wrapper designed to simplify the creation of Telegram bots using the [**smolagents**](https://github.com/huggingface/smolagents) framework from Hugging Face. This wrapper allows you to quickly deploy agents as Telegram bots, where each user interacts with their own persistent agent instance.

**The core idea is that the agent sends its final response back to the user by calling a special tool provided by the wrapper, rather than just returning text.**

## Overview

This project (`SmolAgentsTelegram`) provides a `start_agent_bot` function that handles the underlying `python-telegram-bot` setup. You need to provide:

1.  Your Telegram Bot Token.
2.  A function (`generate_agent_fn`) that creates and returns a `smolagents` agent instance.

**New in this version:**
* The wrapper now injects a special `on_message` tool into your agent via the `generate_agent_fn`.
* Your agent **must** be configured to use this `on_message` tool to send its final reply back to the Telegram user.
* Your `generate_agent_fn` function **must** accept `on_message` and `user_id` arguments and include the `on_message` object in the agent's tool list.

The wrapper automatically manages different agent instances for each unique Telegram chat ID and handles sending the message via the tool. It also includes an optional feature to restrict bot access and a `/get_chat_id` command.

## Features

* **Easy Integration:** Seamlessly integrates with the `smolagents` framework.
* **Tool-Based Response:** Agents respond by calling a dedicated `on_message` tool, allowing for more complex interactions or asynchronous replies.
* **PyPI Package:** Simple installation via `pip`.
* **Multi-User Support:** Automatically creates and manages separate agent instances for each Telegram user (based on chat ID).
* **Stateful Conversations:** Each user interacts with their dedicated agent.
* **Access Control:** Optionally restrict bot usage to specific Telegram chat IDs.
* **Simple Setup:** Requires minimal boilerplate code to get a bot running.
* **Helper Command:** Includes a `/get_chat_id` command for users to easily find their chat ID.
* **Extensible:** Easily customize the type of agent, tools, and models used within the `smolagents` framework.

## Prerequisites

* Python 3.8+
* A Telegram Bot: Create one using [BotFather](https://t.me/botfather) on Telegram to get your `TELEGRAM_TOKEN`.
* (Optional) API keys for specific models or tools (e.g., Hugging Face Hub token).

## Installation

1.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

2.  **Install the package from PyPI:**
    ```bash
    pip install SmolAgentsTelegram
    ```
    This will install the wrapper and its dependencies, including `smolagents` and `python-telegram-bot`.

3.  **(Optional) For Development:**
    If you want to modify the wrapper code itself, clone the repository and install it in editable mode:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    pip install -e .
    ```

## Configuration

1.  Create a file named `.env` in the root directory of your project where you'll run the bot.
2.  Add your Telegram Bot Token to the `.env` file:
    ```dotenv
    TELEGRAM_TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ```
3.  (Optional) Add other required API keys (e.g., `HUGGINGFACE_HUB_TOKEN`).

## Usage

1.  **Create your main Python script** (e.g., `run_bot.py`). Note the changes in `generate_client` function signature and how the `on_message` tool is used.

    ```python
    # run_bot.py
    import os
    from dotenv import load_dotenv
    # Import from the installed SmolAgentsTelegram package
    from sat import start_agent_bot
    # Import from Hugging Face's smolagents
    from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel

    # Load environment variables from .env file
    load_dotenv()

    # --- IMPORTANT CHANGES ---
    # Your function MUST accept 'on_message' and 'user_id' arguments.
    # 'on_message' is a dynamically generated tool that the agent MUST use to reply.
    def generate_client(on_message, user_id):
        """
        Creates a CodeAgent configured to use the provided on_message tool for replies.
        """
        print(f"Creating new agent for user_id: {user_id}")

        # Configure the model
        model = HfApiModel(model_id="google/gemma-3-27b-it") # Ensure access/tokens if needed

        # Configure standard tools
        standard_tools = [DuckDuckGoSearchTool()]

        # --- IMPORTANT ---
        # Add the provided 'on_message' tool to the agent's tool list.
        # The agent needs to be prompted or instructed to call this tool
        # (named 'on_message' with description 'this is the function that MUST be used...')
        # to send its final answer to the user.
        all_tools = standard_tools + [on_message]

        # Create the agent with all tools
        agent = CodeAgent(tools=all_tools, model=model)
        # Consider adding instructions to your agent's system prompt to use the 'on_message' tool for final replies.
        return agent

    if __name__ == "__main__":
        telegram_token = os.environ.get("TELEGRAM_TOKEN")
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN not found. Did you create a .env file?")

        # Optional: Restrict Access (no changes here)
        # allowed_chat_ids = ["123456789", "987654321"]
        # start_agent_bot(telegram_token=telegram_token, generate_agent_fn=generate_client, telegram_chat_ids=allowed_chat_ids)

        print("Starting Telegram bot...")
        # Pass the updated generate_client function
        start_agent_bot(
            telegram_token=telegram_token,
            generate_agent_fn=generate_client # Corrected function name used here
        )

    ```

2.  **Instruct Your Agent:** You **must** ensure your agent (through its system prompt or specific instructions within the conversation) understands that it needs to call the `on_message` tool to send the final reply to the user. The tool's description (`"this is the function that MUST be used to send final answer back to a cusotmer"`) is designed to help with this.

3.  **Run the script:**
    ```bash
    python run_bot.py
    ```

4.  **Interact with your bot on Telegram:**
    * Send a message. You might receive an initial, immediate reply (from the `update.message.reply_text(clt.run(...))` line in the wrapper). This likely contains the agent's raw output or thought process.
    * The **final, user-intended response** will arrive as a separate message, sent when the agent calls the `on_message` tool.
    * Use `/get_chat_id` to find your chat ID if needed.

## Customization

* **Agent Logic:** The main customization is now within your agent's definition and prompting. Ensure it reliably calls the `on_message` tool for its final output.
* **`generate_agent_fn`:** This function *must* now accept `on_message` and `user_id` and *must* include the `on_message` object in the agent's `tools` list.
* **Tools & Models:** You can still customize the other tools and the model used by the agent within `generate_agent_fn` as before.
* **Restricting Access:** Pass `telegram_chat_ids` list to `start_agent_bot`.

## License

This project is licensed under the MIT License.

## Author

* **Viacheslav Kovalevskyi** - viacheslav@kovalevskyi.com