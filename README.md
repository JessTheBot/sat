# Smol Agents Telegram Bot Wrapper (SmolAgentsTelegram)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/SmolAgentsTelegram.svg)](https://badge.fury.io/py/SmolAgentsTelegram)

A Python wrapper designed to simplify the creation of Telegram bots using the [**smolagents**](https://github.com/huggingface/smolagents) framework from Hugging Face. This wrapper allows you to quickly deploy agents as Telegram bots, where each user interacts with their own persistent agent instance.

## Overview

This project (`SmolAgentsTelegram`) provides a `start_agent_bot` function that handles the underlying `python-telegram-bot` setup. You only need to provide:

1.  Your Telegram Bot Token.
2.  A function (`generate_agent_fn`) that creates and returns a `smolagents` agent instance (e.g., `CodeAgent`, `AssistantAgent`).

The wrapper automatically manages different agent instances for each unique Telegram chat ID, ensuring conversations are isolated between users. It also includes an optional feature to restrict bot access to a predefined list of chat IDs and a command to help users find their chat ID.

## Features

* **Easy Integration:** Seamlessly integrates with the `smolagents` framework.
* **PyPI Package:** Simple installation via `pip`.
* **Multi-User Support:** Automatically creates and manages separate agent instances for each Telegram user (based on chat ID).
* **Stateful Conversations:** Each user interacts with their dedicated agent, maintaining conversation context (depending on the agent's implementation).
* **Access Control:** Optionally restrict bot usage to specific Telegram chat IDs.
* **Simple Setup:** Requires minimal boilerplate code to get a bot running.
* **Helper Command:** Includes a `/get_chat_id` command for users to easily find their chat ID.
* **Extensible:** Easily customize the type of agent, tools, and models used within the `smolagents` framework.

## Prerequisites

* Python 3.8+
* A Telegram Bot: Create one using [BotFather](https://t.me/botfather) on Telegram to get your `TELEGRAM_TOKEN`.
* (Optional) API keys for specific models or tools (e.g., Hugging Face Hub token if using private/gated models via `HfApiModel`).

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
3.  (Optional) If your chosen agent/model requires other API keys (like a Hugging Face token for `HfApiModel`), add them to the `.env` file as well.
    ```dotenv
    # Example if needed for private/gated models or rate limits
    # HUGGINGFACE_HUB_TOKEN="YOUR_HF_TOKEN_HERE"
    ```

## Usage

1.  **Create your main Python script** (e.g., `run_bot.py`). Make sure you import `start_agent_bot` from the installed package (`sat` namespace, based on your original code):

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

    # Define a function that creates and returns an agent instance
    # This function will be called for each new user (chat_id)
    def generate_client(user_id):
        """Creates a CodeAgent with Gemma and DuckDuckGo search using smolagents."""
        print(f"Creating new agent for user_id: {user_id}")
        # Configure the model (using HfApiModel from smolagents)
        model = HfApiModel(model_id="google/gemma-3-27b-it") # Ensure access/tokens if needed

        # Configure the tools (using DuckDuckGoSearchTool from smolagents)
        tools = [DuckDuckGoSearchTool()]

        # Create the agent (using CodeAgent from smolagents)
        agent = CodeAgent(tools=tools, model=model)
        return agent

    if __name__ == "__main__":
        # Get the Telegram token from environment variables
        telegram_token = os.environ.get("TELEGRAM_TOKEN")
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables. Did you create a .env file?")

        # --- Optional: Restrict Access ---
        # allowed_chat_ids = ["123456789", "987654321"]
        # start_agent_bot(
        #     telegram_token=telegram_token,
        #     generate_agent_fn=generate_client,
        #     telegram_chat_ids=allowed_chat_ids
        # )
        # --- End Optional ---

        # Start the bot without restrictions
        print("Starting Telegram bot...")
        start_agent_bot(
            telegram_token=telegram_token,
            generate_agent_fn=generate_client
        )

    ```

2.  **Run the script:**
    ```bash
    python run_bot.py
    ```

3.  **Interact with your bot on Telegram:**
    * Find your bot on Telegram.
    * Send it messages. Each message will be processed by the `smolagents` agent instance associated with your chat ID.
    * Use `/get_chat_id` to find your chat ID if needed.

## Customization

* **Different Agents:** Modify the `generate_client` function to return a different type of agent available in `smolagents`.
* **Different Tools:** Change the `tools` list within `generate_client` to use other tools compatible with `smolagents`.
* **Different Models:** Change the `model` instance within `generate_client`. Use other models supported by `smolagents`. Remember to configure any necessary API keys.
* **Restricting Access:** Pass a list of allowed Telegram chat IDs (strings) to `start_agent_bot` using the `telegram_chat_ids` parameter.

## License

This project is licensed under the MIT License.

## Author

* **Viacheslav Kovalevskyi** - viacheslav@kovalevskyi.com