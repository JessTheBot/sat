from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
from telegram.ext import filters

from smolagents import tool


class TelegramBot(object):

    def __init__(self, generate_agent_fn, application, restricted_chat_ids=[]):
        self.clients = {}
        self.generate_agent_fn = generate_agent_fn
        self.restricted_chat_ids = restricted_chat_ids
        self.application = application

    def generate_on_message(self, chat_id):
        @tool
        def on_message(msg: str) -> str:
            """this is the function that MUST be used to send final answer bakc to a cusotmer

            Args:
                msg: msg to sand to a user
            """
            self.application.bot.send_message(chat_id=chat_id, text=msg)
            return "DONE"
        return on_message

    async def message(self, update, context):
        if self.restricted_chat_ids and update and update.message and str(update.message.chat_id) not in self.restricted_chat_ids:
            return
        clt = self.clients.get(update.message.chat_id, None)
        if not clt:
            clt = self.generate_agent_fn(
                on_message=self.generate_on_message(update.message.chat_id),
                user_id=update.message.chat_id)
            self.clients[update.message.chat_id] = clt
        await update.message.reply_text(clt.run(update.message.text))
        

async def get_chat_id(update, context):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")


def start_agent_bot(*, telegram_token, telegram_chat_ids=None, generate_agent_fn):
    application = ApplicationBuilder().token(telegram_token).build()
    bot = TelegramBot(generate_agent_fn, application, None)
    drop_client_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message)
    application.add_handler(drop_client_handler)
    get_chat_id_handler = CommandHandler('get_chat_id', get_chat_id)
    application.add_handler(get_chat_id_handler)   
    application.run_polling()

