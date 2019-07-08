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
        handlers = TelegramBotHandlers(moltin_api)
        dispatcher = self.updater.dispatcher

        dispatcher.add_handler(
            CallbackQueryHandler(handlers.handle_use_reply))
        dispatcher.add_handler(
            CommandHandler('start', handlers.handle_use_reply))
        dispatcher.add_handler(
            MessageHandler(Filters.text, handlers.handle_use_reply))

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

        states_functions = {
            'HANDLE_START': self.handle_start,
            'HANDLE_MENU': self.handle_menu,
            'HANDLE_PRODUCT': self.handle_product
        }
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
        text = 'Please choose: '
        if update.message:
            update.message.reply_text(text, reply_markup=reply_markup)
        else:
            query = update.callback_query
            bot.send_message(
                query.message.chat_id,
                text,
                reply_markup=reply_markup
            )

        return 'HANDLE_MENU'

    def handle_menu(self, bot, update):
        query = update.callback_query

        product = self.moltin_api.get_product_by_id(query.data)

        text = '{}\n{}\n{}'.format(
            product.name,
            product.formatted_price,
            product.description
        )

        if product.variations is None:
            add_to_cart_options = [
                InlineKeyboardButton('Add to cart', callback_data=product.id)
            ]
        else:
            add_to_cart_options = [
                InlineKeyboardButton(variation.name, callback_data=variation.id)
                for variation in product.variations
            ]

        keyboard = [
            add_to_cart_options,
            [
                InlineKeyboardButton('Return', callback_data='return'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if product.main_image_id is None:
            bot.send_message(
                query.message.chat_id,
                text,
                reply_markup=reply_markup
            )
        else:
            file = self.moltin_api.get_file_by_id(
                product.main_image_id)

            bot.send_photo(
                query.message.chat_id,
                photo=file.link,
                caption=text,
                reply_markup=reply_markup
            )

        return 'HANDLE_PRODUCT'

    def handle_product(self, bot, update):

        query = update.callback_query

        bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        if query.data == 'return':
            return self.handle_start(bot, update)