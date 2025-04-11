from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
from telegram.ext import filters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from typing import Callable, List, Any, Dict


class TelegramBot(object):

    def __init__(self, generate_agent_fn, application, restricted_chat_ids=[], app_name="TelegramBot", debug=False):
        self.generate_agent_fn = generate_agent_fn
        self.restricted_chat_ids = restricted_chat_ids
        self.application = application
        self.runners = {}
        self.session_service = InMemorySessionService()
        self.app_name = app_name
        self.debug = debug

    def _create_send_message_tool(self, chat_id: str) -> Callable:
        """
        Factory function to create the tool for sending a message
        back to a specific Telegram chat.
        """
        async def send_telegram_message(message_text: str) -> str:
            """
            Use this tool ONLY to send a message text back to the user
            in the current Telegram chat. This can be used for asking
            clarifying questions, providing intermediate updates,
            or delivering the final answer.

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

    def generate_on_message(self, chat_id):
        async def on_message(msg: str) -> str:
            """This is the function that MUST be used in order to send final answer back to a user.
            You still can repeast same message elserwhere but this is the only way how to make sure
            that user will recieve the message. User will NOT see the message unless it is also send with 
            this function.

            Args:
                msg: msg to sand to a user
            """
            await self.application.bot.send_message(chat_id=chat_id, text=msg)
            return "DONE, message was sent to a user"
        return on_message

    async def message(self, update, context):
        if self.restricted_chat_ids and update and update.message and str(update.message.chat_id) not in self.restricted_chat_ids:
            return
        chat_session = self.session_service.get_session(
            app_name=self.app_name, 
            user_id=str(update.message.chat_id), 
            session_id=str(update.message.chat_id))
        if not chat_session:
            chat_session = self.session_service.create_session(
                app_name=self.app_name, 
                user_id=str(update.message.chat_id), 
                session_id=str(update.message.chat_id))
        
        
        runner_instance = self.runners.get(update.message.chat_id, None)
        if not runner_instance:
            agent = self.generate_agent_fn(
                on_message=self.generate_on_message(update.message.chat_id),
                user_id=update.message.chat_id)
            runner_instance = Runner(
                agent=agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            self.runners[update.message.chat_id] = runner_instance

        if self.debug:
            print(f"message received: {update.message.text}")

        user_content = types.Content(role='user', parts=[types.Part(text=update.message.text)])
        for event in runner_instance.run(
            user_id=str(update.message.chat_id), 
            new_message=user_content, 
            session_id=str(update.message.chat_id)):
            if self.debug:
                print(str(event))
            if event.is_final_response() and event.content and event.content.parts:
                if self.debug:
                    print("Final reponse reached")
                break
        
        

async def get_chat_id(update, context):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")


def start_agent_bot(*, telegram_token, telegram_chat_ids=None, generate_agent_fn, app_name="TelegramBot", debug=False):
    application = ApplicationBuilder().token(telegram_token).build()
    bot = TelegramBot(generate_agent_fn, application, restricted_chat_ids=telegram_chat_ids, app_name=app_name, debug=debug)
    drop_client_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message)
    application.add_handler(drop_client_handler)
    get_chat_id_handler = CommandHandler('get_chat_id', get_chat_id)
    application.add_handler(get_chat_id_handler)   
    application.run_polling()

