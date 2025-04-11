from adkt import start_agent_bot

from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

import os

load_dotenv()

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
  # ... function implementation to fetch status ...
  return {"status": 'processing', "tracking_number": '12312fw'} # Example structure





def generat_client(send_telegram_message_tool, user_id):
    # --- Example Agent using Gemma 2B running via Ollama ---
    return LlmAgent(
        # LiteLLM knows how to connect to a local Ollama server by default
        model=LiteLlm(model="ollama/yasserrmd/Llama-4-Scout-17B-16E-Instruct"), # Standard LiteLLM format for Ollama
        # model="gemini-2.5-pro-preview-03-25",
        name="ollama_gemma_agent",
        instruction="You are Gemma, running locally via Ollama. You are assistent that doing conversation with user but also can provide status of the order. ",
        tools=[lookup_order_status, send_telegram_message_tool]
        # ... other agent parameters
    )


if __name__ == "__main__":
    start_agent_bot(telegram_token=os.environ.get("TELEGRAM_TOKEN"), generate_agent_fn=generat_client, debug=True)