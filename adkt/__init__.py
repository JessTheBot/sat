import asyncio
from telegram import Update, Bot # Import Bot for type hinting
from telegram.ext import Application, ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler # Use Application directly
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session # Import Session for type hinting
from google.genai import types
from google.adk.agents import LlmAgent # Assuming LlmAgent is used
from typing import Callable, List, Any, Dict # For type hints

# Define a type hint for the agent generation function
# It should accept user_id and the generated tool function
AgentGenerator = Callable[[str, Callable], LlmAgent]

class TelegramBot(object):

    def __init__(self,
                 generate_agent_fn: AgentGenerator,
                 application: Application, # Use Application type
                 restricted_chat_ids: List[str] = [],
                 app_name: str = "TelegramBot",
                 debug: bool = False):
        self.generate_agent_fn = generate_agent_fn
        self.restricted_chat_ids = restricted_chat_ids
        self.application = application
        # Store runners keyed by chat_id (string)
        self.runners: Dict[str, Runner] = {}
        self.session_service = InMemorySessionService()
        self.app_name = app_name
        self.debug = debug
        # Ensure the bot instance is available if needed separately
        self.bot: Bot = self.application.bot

    def _create_send_message_tool(self, chat_id: str) -> Callable:
        """
        Factory function to create the tool for sending a message
        back to a specific Telegram chat.
        """
        async def send_telegram_message(message_text: str) -> str:
            """
            Use this tool to send a message text back to the user.

            Args:
                message_text: The text content of the message to send.

            Returns:
                A string indicating success ("Message sent.") or failure ("Error sending message: ...").
            """
            if self.debug:
                print(f"Agent requested sending message via tool to chat {chat_id}: {message_text}")
            try:
                await self.bot.send_message(chat_id=chat_id, text=message_text)
                return "Message sent."
            except Exception as e:
                # Log the error for debugging
                print(f"Error sending message via tool to chat {chat_id}: {e}")
                # Inform the agent that the tool failed
                return f"Error sending message: {e}"
        return send_telegram_message

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Basic validation
        if not update or not update.message or not update.message.chat_id or not update.message.text:
             if self.debug: print("Ignoring update with missing data.")
             return

        chat_id_str = str(update.message.chat_id)
        user_id_str = chat_id_str # Using chat_id as both user_id and session_id

        # --- Authorization ---
        if self.restricted_chat_ids and chat_id_str not in self.restricted_chat_ids:
            if self.debug: print(f"Chat ID {chat_id_str} is restricted.")
            # Maybe send a message back?
            # await self.bot.send_message(chat_id=chat_id_str, text="Sorry, you are not authorized.")
            return

        # --- Session Management ---
        try:
            chat_session: Session = self.session_service.get_session(
                app_name=self.app_name,
                user_id=user_id_str,
                session_id=chat_id_str)
            if not chat_session:
                if self.debug: print(f"Creating new session for chat {chat_id_str}")
                chat_session = self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=user_id_str,
                    session_id=chat_id_str)
        except Exception as e:
             print(f"Error managing session for chat {chat_id_str}: {e}")
             await self.bot.send_message(chat_id=chat_id_str, text="Sorry, there was a session error. Please try again.")
             return

        # --- Runner and Agent Creation (Per-Chat, Lazy Initialization) ---
        runner_instance = self.runners.get(chat_id_str)
        if not runner_instance:
            if self.debug: print(f"Creating new Runner/Agent for chat {chat_id_str}")
            try:
                # Create the specific tool instance for this chat
                send_message_tool = self._create_send_message_tool(chat_id_str)

                # Generate the agent, providing the tool
                agent = self.generate_agent_fn(
                    user_id=user_id_str,
                    # Pass the tool function, agent generator must expect this argument name
                    send_telegram_message_tool=send_message_tool
                )

                # Simple check if agent generation seemed successful
                if not isinstance(agent, LlmAgent):
                     raise TypeError("generate_agent_fn did not return an LlmAgent instance.")

                runner_instance = Runner(
                    agent=agent,
                    app_name=self.app_name,
                    session_service=self.session_service
                )
                self.runners[chat_id_str] = runner_instance
            except Exception as e:
                 print(f"Fatal Error creating agent/runner for chat {chat_id_str}: {e}")
                 # Consider sending an error message to the user
                 await self.bot.send_message(chat_id=chat_id_str, text="Sorry, failed to initialize the agent. Please contact support.")
                 # Prevent further processing for this message
                 return

        # --- Process Message with Runner ---
        if self.debug:
            print(f"Processing message from chat {chat_id_str}: {update.message.text}")

        user_content = types.Content(role='user', parts=[types.Part(text=update.message.text)])
        final_response_from_event = None # Store text from ADK's final event if any

        try:
            # Use 'async for' as runner.run is likely async when involving async tools/models
            async for event in runner_instance.run_async(
                user_id=user_id_str,
                new_message=user_content,
                session_id=chat_id_str):

                if self.debug:
                    # Log the event type and author for better tracing
                    print(f"ADK Event ({chat_id_str}): Author={event.author}, Content={event.content}") # Simplified event logging

                # Handle potential errors reported by ADK event
                if event.error_message:
                    print(f"ADK Runner Error ({chat_id_str}): {event.error_message}")
                    # Decide if you want to notify the user based on ADK errors
                    # await self.bot.send_message(chat_id=chat_id_str, text="An internal processing error occurred.")
                    # Consider breaking or returning based on error severity
                    break # Exit loop on error

                # Check if ADK signals a final response *and* if it contains text
                if event.is_final_response() and event.content and event.content.parts:
                     # Check specifically for text part, as other parts might exist
                     text_part = next((part.text for part in event.content.parts if part.text), None)
                     if text_part:
                        final_response_from_event = text_part
                        if self.debug:
                            print(f"ADK signaled final response with text ({chat_id_str}): {final_response_from_event}")
                        # Don't break here yet, let the runner finish, but capture the text.

            # --- Post-Run Handling ---
            if self.debug:
                 print(f"Runner loop finished for chat {chat_id_str}.")

            # Optional: If ADK provided final text AND the agent didn't already send it via tool, send it now.
            # This is complex logic. A simpler approach might be to *ignore* final_response_from_event
            # if you fully trust the agent to use the tool for *all* user-facing output.
            # For now, let's assume the agent *might* forget the final tool call, so we log if ADK had something.
            if final_response_from_event:
                 if self.debug:
                     print(f"Note: ADK provided final text for chat {chat_id_str}, but we rely on the agent using the tool for output.")
                     # If you wanted to send it as a fallback:
                     # await self.bot.send_message(chat_id=chat_id_str, text=f"Final thought: {final_response_from_event}")


        except Exception as e:
             # Catch errors during the runner.run loop itself
             print(f"Exception during runner.run for chat {chat_id_str}: {e}")
             await self.bot.send_message(chat_id=chat_id_str, text="Sorry, a critical error occurred while processing your request.")
             # Optional: Clean up runner instance on critical failure?
             # self.runners.pop(chat_id_str, None)
             return

# --- start_agent_bot function ---
def start_agent_bot(*,
                    telegram_token: str,
                    telegram_chat_ids: List[str] = None,
                    generate_agent_fn: AgentGenerator, # Pass the function adhering to the signature
                    app_name: str = "TelegramBot",
                    debug: bool = False):

    # Use Application for richer context if needed later
    application = ApplicationBuilder().token(telegram_token).build()

    # Instantiate the Bot wrapper class
    bot_wrapper = TelegramBot(
        generate_agent_fn=generate_agent_fn,
        application=application,
        restricted_chat_ids=telegram_chat_ids or [],
        app_name=app_name,
        debug=debug
    )

    # Add handlers
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, bot_wrapper.message)
    application.add_handler(message_handler)

    get_chat_id_handler = CommandHandler('get_chat_id', get_chat_id) # Ensure get_chat_id is defined
    application.add_handler(get_chat_id_handler)

    print(f"Starting Telegram bot polling for app '{app_name}'...")
    # Run the bot
    application.run_polling()

# --- Placeholder for get_chat_id ---
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
     if update.message:
        chat_id = update.message.chat_id
        # Consider permissions before sending
        await update.message.reply_text(f"This chat's ID is: {chat_id}")

