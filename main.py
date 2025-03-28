from sat import start_agent_bot

from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel
from dotenv import load_dotenv

import os

load_dotenv()


def generat_client(on_message, user_id):
    model = HfApiModel(model_id="google/gemma-3-27b-it")
    return CodeAgent(tools=[DuckDuckGoSearchTool(), on_message], model=model)


if __name__ == "__main__":
    start_agent_bot(telegram_token=os.environ.get("TELEGRAM_TOKEN"), generate_agent_fn=generat_client)