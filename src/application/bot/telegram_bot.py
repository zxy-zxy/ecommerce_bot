from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Updater,
    Filters,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from application.models import User
from application.ecommerce_api.moltin_api.moltin import MoltinApi
from application.bot.utils import chunks


class TelegramBot:
    def __init__(self, token: str, moltin_api: MoltinApi):
        self.updater = Updater(token=token)
        bot_handlers = TelegramBotHandlers(moltin_api)
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(
            CallbackQueryHandler(bot_handlers.handle_use_reply))
        dispatcher.add_handler(
            MessageHandler(Filters.text, bot_handlers.handle_use_reply))
        dispatcher.add_handler(
            CommandHandler('start', bot_handlers.handle_use_reply))

    def start(self):
        self.updater.start_polling()


class TelegramBotHandlers:
    def __init__(self, moltin_api: MoltinApi):
        self.moltin_api = moltin_api

    def handle_use_reply(self, bot, update):
        if update.message:
            user_reply = update.message.text
            chat_id = update.message.chat_id
        elif update.callback_query:
            user_reply = update.callback_query.data
            chat_id = update.callback_query.message.chat_id
        else:
            return

        user = User(chat_id)

        if user_reply == '/start':
            user_state = 'HANDLE_START'
        else:
            user_state = user.get_state_from_db()

        states_functions = {'HANDLE_START': self.handle_start, 'HANDLE_MENU': self.handle_menu}
        state_handler = states_functions[user_state]

        try:
            next_state = state_handler(bot, update)
            user.save_state_to_db(next_state)
        except Exception as err:
            print(err)

    def handle_start(self, bot, update):

        keyboard_row_buttons_width = 2
        products = self.moltin_api.get_products()
        products_chunks = chunks(products, keyboard_row_buttons_width)

        keyboard = [
            [
                InlineKeyboardButton(product.name, callback_data=product.id)
                for product in product_chunk
            ]
            for product_chunk in products_chunks
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('Please choose:', reply_markup=reply_markup)
        return 'HANDLE_MENU'

    def handle_menu(self, bot, update):
        query = update.callback_query

        product = self.moltin_api.get_product(query.data)

        bot.edit_message_text(
            text='{}\n{}\n{}'.format(
                product.name,
                product.formatted_price,
                product.description
            ),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )

        return 'HANDLE_START'
